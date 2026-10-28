"""Explicitly trusted local model loading and strict five-input batch prediction."""

import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline

from freightguard.validate_data import FEATURE_COLUMNS, SHIPPING_MODES


class ModelArtifactError(ValueError):
    """A safe artifact or prediction-schema error with no record contents."""


def prediction_features(frame: pd.DataFrame) -> pd.DataFrame:
    if (
        frame.empty
        or not frame.columns.is_unique
        or set(frame.columns) != set(FEATURE_COLUMNS)
    ):
        raise ModelArtifactError(
            "Prediction requires exactly the five approved fields."
        )
    data = frame.loc[:, list(FEATURE_COLUMNS)].copy()
    if data.isna().any().any():
        raise ModelArtifactError("Prediction fields cannot be missing.")
    days = pd.to_numeric(data[FEATURE_COLUMNS[0]], errors="coerce")
    if not (days.notna() & np.isfinite(days) & days.ge(0) & days.mod(1).eq(0)).all():
        raise ModelArtifactError(
            "Scheduled shipping days must be nonnegative integers."
        )
    data[FEATURE_COLUMNS[0]] = days
    for column in FEATURE_COLUMNS[1:]:
        if (
            not data[column]
            .map(lambda value: isinstance(value, str) and bool(value.strip()))
            .all()
        ):
            raise ModelArtifactError(
                "Categorical prediction fields must be nonempty text."
            )
    if not data["Shipping Mode"].isin(SHIPPING_MODES).all():
        raise ModelArtifactError("Unsupported shipping mode.")
    return data


@dataclass
class PredictionModel:
    pipeline: Pipeline
    threshold: float
    model_version: str

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        features = prediction_features(frame)
        probability = self.pipeline.predict_proba(features)[:, 1]
        return pd.DataFrame(
            {
                "late_probability": probability,
                "late_prediction": (probability >= self.threshold).astype(int),
            },
            index=frame.index,
        )


def load_model(
    path: Path, *, expected_sha256: str, trusted: bool = False
) -> PredictionModel:
    """Hashes detect corruption, not malicious publishers. Pickle can execute code.

    Only opt in for an artifact you created locally or independently trust. Never
    call this on uploads/downloads merely because their publisher supplied a hash.
    """
    if not trusted:
        raise ModelArtifactError(
            "Refusing serialized model without explicit local trust."
        )
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ModelArtifactError("A valid independently checked SHA-256 is required.")
    try:
        content = path.read_bytes()
    except OSError:
        raise ModelArtifactError("Cannot read local model artifact.") from None
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ModelArtifactError("Model artifact checksum mismatch.")
    # Deserialize the same verified bytes; do not reopen a potentially changed path.
    payload = joblib.load(io.BytesIO(content))
    if (
        not isinstance(payload, dict)
        or payload.get("artifact_schema_version") != 1
        or payload.get("sklearn_version") != sklearn.__version__
        or payload.get("feature_columns") != list(FEATURE_COLUMNS)
        or not isinstance(payload.get("pipeline"), Pipeline)
        or not isinstance(payload.get("model_version"), str)
        or not isinstance(payload.get("threshold"), (float, int))
        or not 0 < payload["threshold"] < 1
    ):
        raise ModelArtifactError("Unsupported model artifact schema.")
    pipeline = payload["pipeline"]
    if (
        list(pipeline.named_steps) != ["preprocessor", "classifier"]
        or list(pipeline.feature_names_in_) != list(FEATURE_COLUMNS)
        or pipeline.classes_.tolist() != [0, 1]
    ):
        raise ModelArtifactError(
            "Model pipeline does not match the prediction contract."
        )
    return PredictionModel(pipeline, payload["threshold"], payload["model_version"])
