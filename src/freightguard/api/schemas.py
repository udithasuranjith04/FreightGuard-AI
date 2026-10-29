"""Strict public schema and explicit mapping to the five approved model inputs."""

import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

FEATURE_MAP = {
    "scheduled_shipping_days": "Days for shipment (scheduled)",
    "shipping_mode": "Shipping Mode",
    "market": "Market",
    "order_region": "Order Region",
    "order_country": "Order Country",
}
LIMITATIONS = [
    "Educational model: primarily shipping-plan patterns, not validated order-specific operational alerts.",
    "Risk is conditional on eventual non-cancellation; the historical retail dataset may not represent current shipments.",
    "The frozen 0.40 threshold predicted every held-out test order late; scores are experimental, not guaranteed probabilities.",
]


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    scheduled_shipping_days: int = Field(
        ge=0, le=4, description="Scheduled days, integer 0–4; never actual duration."
    )
    shipping_mode: Literal["Standard Class", "First Class", "Second Class", "Same Day"]
    market: Literal["Africa", "Europe", "LATAM", "Pacific Asia", "USCA"]
    order_region: str = Field(min_length=2, max_length=80)
    order_country: str = Field(min_length=2, max_length=80)

    @field_validator("order_region", "order_country")
    @classmethod
    def broad_geography(cls, value: str) -> str:
        value = unicodedata.normalize("NFC", value.strip())
        if (
            len(value) < 2
            or not any(char.isalpha() for char in value)
            or not all(
                char.isalpha()
                or unicodedata.category(char).startswith("M")
                or char in " .'-’()"
                for char in value
            )
        ):
            raise ValueError(
                "Use bounded broad geography names, without contact details."
            )
        return value

    def model_features(self) -> dict:
        return {feature: getattr(self, field) for field, feature in FEATURE_MAP.items()}


class PredictionResponse(BaseModel):
    risk_score: float = Field(ge=0, le=1)
    experimental_prediction: Literal["late", "not_late"]
    model_version: Literal["v1"]
    threshold: float
    experimental: Literal[True] = True
    operationally_validated: Literal[False] = False
    warnings: list[str]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    model_ready: bool


class ModelInfoResponse(BaseModel):
    model_version: Literal["v1"] = "v1"
    model_ready: bool
    readiness_status: Literal["ready_for_educational_demo", "unavailable"]
    unavailable_reason: str | None
    operationally_validated: Literal[False] = False
    threshold: float
    approved_features: list[str]
    request_fields: list[str]
    limitations: list[str]
    allowed_categories: dict[str, list[str]]


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorDetail
