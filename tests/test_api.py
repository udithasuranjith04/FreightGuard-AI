"""API behavior tests use synthetic requests and a stub model, never private rows."""

import logging
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import freightguard.api.app as api_module
from freightguard.api.app import create_app
from freightguard.api.settings import Settings
from freightguard.model_artifact import ModelArtifactError
from freightguard.validate_data import FEATURE_COLUMNS

PAYLOAD = {
    "scheduled_shipping_days": 4,
    "shipping_mode": "Standard Class",
    "market": "Europe",
    "order_region": "Western Europe",
    "order_country": "France",
}


class EducationalStub:
    model_version = "v1"
    threshold = 0.4

    def __init__(self):
        encoder = SimpleNamespace(
            categories_=[["Standard Class"], ["Europe"], ["Western Europe"], ["France"]]
        )
        preprocessor = SimpleNamespace(named_transformers_={"categorical": encoder})
        self.pipeline = SimpleNamespace(named_steps={"preprocessor": preprocessor})
        self.calls = 0

    def predict(self, frame):
        assert list(frame.columns) == list(FEATURE_COLUMNS)
        self.calls += 1
        return pd.DataFrame({"late_probability": [0.7], "late_prediction": [1]})


@pytest.fixture
def configured(tmp_path, monkeypatch):
    artifact = tmp_path / "synthetic.joblib"
    artifact.write_bytes(b"stub artifact, never deserialized")
    settings = Settings(
        model_path=artifact, trust_local_model=True, model_sha256="a" * 64
    )
    model = EducationalStub()
    loads = []

    def loader(path, *, expected_sha256, trusted):
        assert path == artifact and trusted and expected_sha256 == "a" * 64
        loads.append("loaded")
        return model

    monkeypatch.setattr(api_module, "load_model", loader)
    return settings, model, loads


def test_model_loaded_only_at_startup_and_predictions_are_experimental(configured):
    settings, model, loads = configured
    app = create_app(settings)
    assert loads == []
    with TestClient(app) as client:
        assert loads == ["loaded"]
        assert client.get("/health").json() == {"status": "ok", "model_ready": True}
        info = client.get("/model/info").json()
        assert info["model_version"] == "v1"
        assert info["approved_features"] == list(FEATURE_COLUMNS)
        assert info["readiness_status"] == "ready_for_educational_demo"
        assert info["operationally_validated"] is False
        assert info["threshold"] == 0.4
        assert any("shipping-plan" in line for line in info["limitations"])
        first = client.post("/predict", json=PAYLOAD)
        assert first.status_code == 200
        result = first.json()
        assert result["risk_score"] == 0.7
        assert result["experimental_prediction"] == "late"
        assert result["experimental"] is True
        assert result["operationally_validated"] is False
        assert result["threshold"] == 0.4
        assert client.post("/predict", json=PAYLOAD).json() == result
        assert loads == ["loaded"] and model.calls == 2
    assert app.state.model is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("scheduled_shipping_days", -1),
        ("scheduled_shipping_days", 5),
        ("scheduled_shipping_days", "4"),
        ("scheduled_shipping_days", 4.0),
        ("scheduled_shipping_days", True),
        ("scheduled_shipping_days", None),
        ("shipping_mode", "private-unknown-mode"),
        ("market", "private-unknown-market"),
        ("order_country", "person@example.com"),
        ("order_country", " "),
        ("order_country", "x" * 81),
        ("order_country", {"Customer Email": "private-secret"}),
        ("order_region", "Western\nEurope"),
        ("order_region", None),
    ],
)
def test_invalid_fields_rejected_without_echoing_values(configured, field, value):
    settings, model, _ = configured
    with TestClient(create_app(settings)) as client:
        response = client.post("/predict", json={**PAYLOAD, field: value})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert "private-" not in response.text and "person@example.com" not in response.text
    assert model.calls == 0


@pytest.mark.parametrize(
    "extra",
    [
        "Customer Email",
        "Customer Password",
        "Late_delivery_risk",
        "Days for shipping (real)",
        "Delivery Status",
        "private-key-name",
    ],
)
def test_extra_sensitive_and_outcome_fields_rejected(configured, extra, caplog):
    settings, model, _ = configured
    with caplog.at_level(logging.INFO), TestClient(create_app(settings)) as client:
        response = client.post("/predict", json={**PAYLOAD, extra: "private-secret"})
    assert response.status_code == 422
    assert response.json()["error"]["fields"] == ["request"]
    assert "private-" not in response.text
    assert all("private-" not in record.getMessage() for record in caplog.records)
    assert model.calls == 0


def test_missing_required_fields_and_malformed_json_are_sanitized(configured):
    settings, model, _ = configured
    with TestClient(create_app(settings)) as client:
        missing = client.post("/predict", json={})
        assert missing.status_code == 422
        assert set(missing.json()["error"]["fields"]) == set(PAYLOAD)
        malformed = client.post(
            "/predict",
            content='{"private-secret":',
            headers={"Content-Type": "application/json"},
        )
        assert malformed.status_code == 422 and "private-secret" not in malformed.text
    assert model.calls == 0


@pytest.mark.parametrize("field", ["order_country", "order_region"])
def test_unknown_geography_rejected_without_value_echo(configured, field):
    settings, model, _ = configured
    with TestClient(create_app(settings)) as client:
        response = client.post("/predict", json={**PAYLOAD, field: "Synthetic Unknown"})
    assert response.status_code == 422
    assert response.json()["error"]["fields"] == [field]
    assert "Synthetic Unknown" not in response.text
    assert model.calls == 0


@pytest.mark.parametrize(
    ("trust", "checksum", "present", "reason"),
    [
        (False, "a" * 64, True, "trust_not_enabled"),
        (True, "", True, "checksum_not_configured"),
        (True, "invalid", True, "checksum_not_configured"),
        (True, "a" * 64, False, "artifact_missing"),
    ],
)
def test_unavailable_model_keeps_health_and_info_working(
    tmp_path, monkeypatch, trust, checksum, present, reason
):
    path = tmp_path / "private-model-path.joblib"
    if present:
        path.write_bytes(b"not deserialized")

    def forbidden(*args, **kwargs):
        pytest.fail("Must not attempt model load")

    monkeypatch.setattr(api_module, "load_model", forbidden)
    settings = Settings(model_path=path, trust_local_model=trust, model_sha256=checksum)
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").json()["model_ready"] is False
        info = client.get("/model/info")
        assert info.status_code == 200 and info.json()["unavailable_reason"] == reason
        response = client.post("/predict", json=PAYLOAD)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"
    assert "private-" not in response.text + info.text


@pytest.mark.parametrize(
    "failure",
    [
        ModelArtifactError("private-checksum-details"),
        RuntimeError("private-filesystem-path /Users/example/secrets"),
    ],
)
def test_loading_failures_are_sanitized(configured, monkeypatch, caplog, failure):
    settings, _, _ = configured

    def broken(*args, **kwargs):
        raise failure

    monkeypatch.setattr(api_module, "load_model", broken)
    with caplog.at_level(logging.INFO), TestClient(create_app(settings)) as client:
        info = client.get("/model/info")
        assert info.json()["unavailable_reason"] == "model_load_failed"
        response = client.post("/predict", json=PAYLOAD)
    assert response.status_code == 503
    assert "private-" not in response.text + info.text + caplog.text


@pytest.mark.parametrize(
    ("attribute", "value"), [("threshold", 0.5), ("model_version", "v2")]
)
def test_startup_rejects_changes_to_frozen_contract(configured, attribute, value):
    settings, model, _ = configured
    setattr(model, attribute, value)
    with TestClient(create_app(settings)) as client:
        assert (
            client.get("/model/info").json()["unavailable_reason"]
            == "frozen_contract_mismatch"
        )
        assert client.post("/predict", json=PAYLOAD).status_code == 503


def test_unexpected_prediction_errors_are_sanitized(configured, monkeypatch, caplog):
    settings, model, _ = configured

    def broken(frame):
        raise RuntimeError("private-payload /Users/example/private-path")

    monkeypatch.setattr(model, "predict", broken)
    with caplog.at_level(logging.INFO), TestClient(create_app(settings)) as client:
        response = client.post("/predict", json=PAYLOAD)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "private-" not in response.text + caplog.text
    assert "Traceback" not in caplog.text


def test_cors_explicit_origin_allowlist(configured):
    settings, _, _ = configured
    with TestClient(create_app(settings)) as client:
        allowed = client.options(
            "/predict",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
        denied = client.options(
            "/predict",
            headers={
                "Origin": "https://unapproved.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert denied.status_code == 400 and "error" in denied.json()
        assert "access-control-allow-origin" not in denied.headers
        invalid = client.post(
            "/predict", json={}, headers={"Origin": "http://localhost:5173"}
        )
        assert invalid.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*.example.com",
        "https://user:secret@example.com",
        "https://example.com/path",
    ],
)
def test_invalid_cors_config_is_rejected(origin):
    with pytest.raises(ValueError, match="CORS requires explicit"):
        Settings(cors_origins=(origin,))


def test_content_type_body_limit_and_other_errors_are_consistent(configured):
    settings, model, _ = configured
    with TestClient(create_app(settings)) as client:
        responses = [
            client.post(
                "/predict",
                content="private-body",
                headers={"Content-Type": "text/plain"},
            ),
            client.post(
                "/predict",
                content=b"x" * 17000,
                headers={"Content-Type": "application/json"},
            ),
            client.post(
                "/predict",
                content=iter([b"x" * 9000, b"x" * 9000]),
                headers={"Content-Type": "application/json"},
            ),
            client.get("/private-path"),
            client.get("/predict"),
        ]
    assert [response.status_code for response in responses] == [415, 413, 413, 404, 405]
    for response in responses:
        assert set(response.json()) == {"error"}
        assert "private-" not in response.text
    assert model.calls == 0


def test_openapi_documents_only_approved_inputs_and_errors(configured):
    settings, _, _ = configured
    with TestClient(create_app(settings)) as client:
        assert client.get("/docs").status_code == 200
        schema = client.get("/openapi.json").json()
    request = schema["components"]["schemas"]["PredictionRequest"]
    assert set(request["properties"]) == set(PAYLOAD)
    assert request["additionalProperties"] is False
    response = schema["paths"]["/predict"]["post"]["responses"]
    assert set(response) >= {"200", "422", "503"}


def test_settings_read_environment_without_implicit_trust(monkeypatch):
    monkeypatch.delenv("FREIGHTGUARD_TRUST_LOCAL_MODEL", raising=False)
    monkeypatch.setenv("FREIGHTGUARD_CORS_ORIGINS", "https://demo.example")
    settings = Settings.from_env()
    assert settings.trust_local_model is False
    assert settings.cors_origins == ("https://demo.example",)


@pytest.mark.parametrize("categories", [[], [["Standard Class"]], [[], [], [], []]])
def test_incomplete_category_contract_is_not_ready(configured, categories):
    settings, model, _ = configured
    encoder = model.pipeline.named_steps["preprocessor"].named_transformers_[
        "categorical"
    ]
    encoder.categories_ = categories
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").json()["model_ready"] is False
        assert client.post("/predict", json=PAYLOAD).status_code == 503


@pytest.mark.parametrize(
    "origin", ["http://localhost:5173", "https://unapproved.example"]
)
def test_unexpected_errors_keep_cors_policy_and_security_headers(
    configured, monkeypatch, origin
):
    settings, model, _ = configured

    def broken(frame):
        raise RuntimeError("private-details")

    monkeypatch.setattr(model, "predict", broken)
    with TestClient(create_app(settings)) as client:
        response = client.post("/predict", json=PAYLOAD, headers={"Origin": origin})
    assert response.status_code == 500
    assert response.headers.get("access-control-allow-origin") == (
        origin if origin in settings.cors_origins else None
    )
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "private-details" not in response.text


def test_real_loader_checksum_failure_never_deserializes(tmp_path, monkeypatch):
    artifact = tmp_path / "pipeline.joblib"
    artifact.write_bytes(b"synthetic untrusted bytes")

    def forbidden(*args, **kwargs):
        pytest.fail("Checksum failure must happen before deserialization")

    monkeypatch.setattr("freightguard.model_artifact.joblib.load", forbidden)
    settings = Settings(
        model_path=artifact, trust_local_model=True, model_sha256="0" * 64
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/model/info").json()["unavailable_reason"] == (
            "model_load_failed"
        )
        assert client.post("/predict", json=PAYLOAD).status_code == 503
