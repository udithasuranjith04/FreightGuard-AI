"""FastAPI application factory with one trusted model load per process lifespan."""

import logging
import re
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from freightguard.api.schemas import (
    FEATURE_MAP,
    LIMITATIONS,
    ErrorResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
)
from freightguard.api.settings import FROZEN_THRESHOLD, MODEL_VERSION, Settings
from freightguard.model_artifact import load_model

LOGGER = logging.getLogger(__name__)
ERRORS = {
    400: ("bad_request", "The request could not be processed."),
    404: ("not_found", "Endpoint not found."),
    405: ("method_not_allowed", "Method not allowed for this endpoint."),
    413: ("payload_too_large", "Prediction request exceeds the 16 KiB limit."),
    415: ("unsupported_media_type", "Prediction requests require application/json."),
    422: (
        "validation_error",
        "Use exactly the five documented fields with valid values.",
    ),
    500: ("internal_error", "The request could not be completed."),
    503: ("model_unavailable", "Educational model is unavailable; check /model/info."),
}


def error_response(status: int, fields: list[str] | None = None) -> JSONResponse:
    code, message = ERRORS.get(status, ERRORS[400])
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "fields": fields or []}},
    )


class PredictionBodyLimit:
    """Bound received bytes, including chunked requests, before JSON parsing."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["path"] != "/predict"
            or scope["method"] != "POST"
        ):
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        if (
            headers.get(b"content-type", b"").split(b";")[0].strip().lower()
            != b"application/json"
        ):
            await error_response(415)(scope, receive, send)
            return
        total = 0

        async def limited_receive():
            nonlocal total
            message = await receive()
            total += len(message.get("body", b""))
            if total > 16 * 1024:
                raise HTTPException(status_code=413)
            return message

        await self.app(scope, limited_receive, send)


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.model = None
        application.state.known_categories = {}
        reason = None
        if not config.trust_local_model:
            reason = "trust_not_enabled"
        elif not re.fullmatch(r"[0-9a-f]{64}", config.model_sha256):
            reason = "checksum_not_configured"
        else:
            try:
                if not config.model_path.is_file():
                    reason = "artifact_missing"
                else:
                    model = load_model(
                        config.model_path,
                        expected_sha256=config.model_sha256,
                        trusted=True,
                    )
                    if (
                        model.model_version != MODEL_VERSION
                        or model.threshold != FROZEN_THRESHOLD
                    ):
                        reason = "frozen_contract_mismatch"
                    else:
                        encoder = model.pipeline.named_steps[
                            "preprocessor"
                        ].named_transformers_["categorical"]
                        application.state.known_categories = {
                            field: frozenset(values)
                            for field, values in zip(
                                list(FEATURE_MAP)[1:], encoder.categories_
                            )
                        }
                        application.state.model = model
            except Exception:  # noqa: BLE001 - sanitize all artifact/request failures
                # Never log exception repr/trace: trusted artifact errors may contain paths.
                reason = "model_load_failed"
        application.state.unavailable_reason = reason
        if reason:
            LOGGER.warning("Educational model unavailable: %s", reason)
        else:
            LOGGER.info(
                "Educational model v1 loaded once; operational validation is false."
            )
        try:
            yield
        finally:
            application.state.model = None
            application.state.known_categories = {}

    api = FastAPI(
        title="FreightGuard AI — Educational Inference API",
        version="0.1.0",
        description="Serves frozen educational model v1. Not operationally validated.",
        lifespan=lifespan,
    )
    api.add_middleware(PredictionBodyLimit)
    api.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @api.middleware("http")
    async def sanitized_errors(request: Request, call_next):
        try:
            response = await call_next(request)
            if response.status_code >= 400 and not response.headers.get(
                "content-type", ""
            ).startswith("application/json"):
                return error_response(response.status_code)
            return response
        except Exception:  # noqa: BLE001 - sanitize all artifact/request failures
            LOGGER.error("API request failed; payload and exception details omitted.")
            return error_response(500)

    @api.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        fields = sorted(
            {
                str(error["loc"][1])
                if len(error["loc"]) > 1 and error["loc"][1] in FEATURE_MAP
                else "request"
                for error in exc.errors()
            }
        )
        return error_response(422, fields)

    @api.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        response = error_response(exc.status_code)
        if exc.status_code == 405 and exc.headers and "Allow" in exc.headers:
            response.headers["Allow"] = exc.headers["Allow"]
        return response

    @api.get("/health", response_model=HealthResponse)
    def health(request: Request):
        return HealthResponse(model_ready=request.app.state.model is not None)

    @api.get("/model/info", response_model=ModelInfoResponse)
    def model_info(request: Request):
        ready = request.app.state.model is not None
        return ModelInfoResponse(
            model_ready=ready,
            readiness_status="ready_for_educational_demo" if ready else "unavailable",
            unavailable_reason=request.app.state.unavailable_reason,
            threshold=FROZEN_THRESHOLD,
            approved_features=list(FEATURE_MAP.values()),
            request_fields=list(FEATURE_MAP),
            limitations=LIMITATIONS,
            allowed_categories={
                field: sorted(values)
                for field, values in request.app.state.known_categories.items()
            },
        )

    @api.post(
        "/predict",
        response_model=PredictionResponse,
        responses={
            status: {"model": ErrorResponse} for status in (413, 415, 422, 500, 503)
        },
    )
    def predict(payload: PredictionRequest, request: Request):
        model = request.app.state.model
        if model is None:
            raise HTTPException(status_code=503)
        unseen = [
            field
            for field, values in request.app.state.known_categories.items()
            if getattr(payload, field) not in values
        ]
        if unseen:
            return error_response(422, sorted(unseen))
        result = model.predict(pd.DataFrame([payload.model_features()])).iloc[0]
        return PredictionResponse(
            risk_score=float(result["late_probability"]),
            experimental_prediction="late"
            if int(result["late_prediction"]) == 1
            else "not_late",
            model_version=model.model_version,
            threshold=model.threshold,
            warnings=list(LIMITATIONS),
        )

    return api


app = create_app()
