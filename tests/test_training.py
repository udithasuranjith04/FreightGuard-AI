"""Training/serialization tests use only invented data and local temporary files."""

import json

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from freightguard.evaluation import evaluate_probabilities, subgroup_metrics
from freightguard.model_artifact import (
    ModelArtifactError,
    load_model,
    prediction_features,
)
from freightguard.prepare_data import chronological_splits
from freightguard.train_model import (
    DEFAULT_RUN_DIR,
    file_sha256,
    run_training,
    select_model,
)
from freightguard.validate_data import (
    DEFAULT_DATA_PATH,
    FEATURE_COLUMNS,
    DatasetValidationError,
)


@pytest.fixture
def training_csv(tmp_path):
    rows = []
    for period, month, country in (
        ("2016", "6", "Synthetic Train"),
        ("2017", "3", "Synthetic Validation"),
        ("2017", "9", "Synthetic Test"),
    ):
        for day in range(1, 25):
            risk = int(day % 3 != 0)
            days = 1 if risk else 4
            rows.append(
                {
                    "Order Id": len(rows) + 1,
                    "Order Item Id": len(rows) + 1,
                    "order date (DateOrders)": f"{month}/{day}/{period} 12:00",
                    "Late_delivery_risk": risk,
                    "Delivery Status": "Late delivery" if risk else "Shipping on time",
                    "Order Status": "COMPLETE",
                    "Days for shipping (real)": days + risk,
                    "Days for shipment (scheduled)": days,
                    "Shipping Mode": "First Class" if risk else "Standard Class",
                    "Market": "Synthetic Market",
                    "Order Region": "Synthetic Region",
                    "Order Country": country,
                    "Customer Email": "private-sentinel",
                }
            )
    path = tmp_path / "synthetic.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_known_metrics_and_calibration():
    assert DEFAULT_RUN_DIR.is_relative_to(DEFAULT_DATA_PATH.parents[1] / "processed")
    metrics = evaluate_probabilities(
        pd.Series([0, 0, 1, 1]), np.array([0.1, 0.7, 0.4, 0.9]), 0.5
    )
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["accuracy"] == metrics["precision"] == metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert sum(row["orders"] for row in metrics["calibration_bins"]) == 4
    assert metrics["brier_score"] == pytest.approx((0.01 + 0.49 + 0.36 + 0.01) / 4)
    single = evaluate_probabilities(pd.Series([1, 1]), np.array([1.0, 1.0]), 0.5)
    assert single["roc_auc"] is None and single["pr_auc"] is None


def test_reproducible_selection_and_train_only_vocabulary(training_csv):
    frame = pd.read_csv(training_csv)
    splits, _ = chronological_splits(frame)
    first = select_model(splits["train"], splits["validation"])
    second = select_model(splits["train"], splits["validation"])
    assert first.report == second.report
    selected_f1 = first.report["validation_candidates"][first.name][
        "selected_threshold_metrics"
    ]["f1"]
    assert selected_f1 == max(
        value["selected_threshold_metrics"]["f1"]
        for value in first.report["validation_candidates"].values()
    )
    assert set(first.report["validation_candidates"]) == {
        "dummy_majority",
        "logistic_regression",
        "random_forest",
    }
    np.testing.assert_array_equal(
        first.pipeline.predict_proba(splits["validation"].X),
        second.pipeline.predict_proba(splits["validation"].X),
    )
    encoder = first.pipeline.named_steps["preprocessor"].named_transformers_[
        "categorical"
    ]
    assert encoder.categories_[-1].tolist() == ["Synthetic Train"]
    assert list(first.pipeline.feature_names_in_) == list(FEATURE_COLUMNS)
    assert (
        first.report["validation_candidates"]["dummy_majority"]["at_0_50"]["recall"]
        == 1
    )
    # Changing the entire held-out cohort cannot affect selection.
    changed = frame.copy()
    mask = changed["Order Country"].eq("Synthetic Test")
    changed.loc[mask, "Order Country"] = "Another Test Geography"
    changed.loc[mask, "Late_delivery_risk"] = (
        1 - changed.loc[mask, "Late_delivery_risk"]
    )
    changed.loc[mask, "Days for shipping (real)"] = (
        changed.loc[mask, "Days for shipment (scheduled)"]
        + changed.loc[mask, "Late_delivery_risk"]
    )
    changed.loc[mask, "Delivery Status"] = changed.loc[mask, "Late_delivery_risk"].map(
        {0: "Shipping on time", 1: "Late delivery"}
    )
    altered, _ = chronological_splits(changed)
    third = select_model(altered["train"], altered["validation"])
    assert third.report == first.report


def test_final_test_is_predicted_once_and_completed_runs_replay(
    training_csv, tmp_path, monkeypatch
):
    calls = []
    original = Pipeline.predict_proba

    def tracked(self, X, *args, **kwargs):
        if X["Order Country"].eq("Synthetic Test").any():
            calls.append("test")
        return original(self, X, *args, **kwargs)

    monkeypatch.setattr(Pipeline, "predict_proba", tracked)
    run = tmp_path / "run"
    first = run_training(training_csv, run)
    frozen = (run / "selection.json").read_bytes()
    monkeypatch.setattr(
        joblib, "load", lambda *args, **kwargs: pytest.fail("No automatic unpickling")
    )
    second = run_training(training_csv, run)
    assert calls == ["test"]
    assert first == second
    assert (run / "selection.json").read_bytes() == frozen
    assert first["test_evaluation_count"] == 1
    assert "private-sentinel" not in json.dumps(first)
    assert (run / "test_evaluation.started").is_file()


def test_trusted_loading_prediction_contract_and_no_personal_artifact_fields(
    training_csv, tmp_path
):
    run = tmp_path / "run"
    report = run_training(training_csv, run)
    artifact = run / "pipeline.joblib"
    with pytest.raises(ModelArtifactError, match="explicit local trust"):
        load_model(artifact, expected_sha256=report["artifact_sha256"])
    model = load_model(
        artifact, expected_sha256=report["artifact_sha256"], trusted=True
    )
    X = pd.read_csv(training_csv).loc[:1, list(FEATURE_COLUMNS)].copy()
    X["Order Country"] = "Unknown Geography"
    prediction = model.predict(X)
    assert list(prediction.columns) == ["late_probability", "late_prediction"]
    assert prediction["late_probability"].between(0, 1).all()
    assert prediction["late_prediction"].isin([0, 1]).all()
    encoder = model.pipeline.named_steps["preprocessor"].named_transformers_[
        "categorical"
    ]
    assert all("private-sentinel" not in str(values) for values in encoder.categories_)
    assert model.model_version == "v1"
    X["Customer Email"] = "private-sentinel"
    with pytest.raises(ModelArtifactError, match="exactly the five"):
        model.predict(X)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("Days for shipment (scheduled)", -1),
        ("Days for shipment (scheduled)", "private-invalid"),
        ("Order Country", None),
        ("Order Country", " "),
        ("Shipping Mode", "private-invalid"),
    ],
)
def test_invalid_prediction_values_fail_safely(training_csv, tmp_path, column, value):
    run = tmp_path / "run"
    report = run_training(training_csv, run)
    model = load_model(
        run / "pipeline.joblib", expected_sha256=report["artifact_sha256"], trusted=True
    )
    X = pd.read_csv(training_csv).loc[:1, list(FEATURE_COLUMNS)].astype(object)
    X.loc[0, column] = value
    with pytest.raises(ModelArtifactError) as error:
        model.predict(X)
    assert "private-" not in str(error.value)


def test_hash_mismatch_is_rejected_before_deserialization(tmp_path, monkeypatch):
    path = tmp_path / "untrusted.joblib"
    path.write_bytes(b"not a model")
    monkeypatch.setattr(joblib, "load", lambda *args: pytest.fail("Must not unpickle"))
    with pytest.raises(ModelArtifactError, match="checksum mismatch"):
        load_model(path, expected_sha256="0" * 64, trusted=True)


def test_prediction_schema_rejects_missing_duplicate_and_empty_fields(training_csv):
    X = pd.read_csv(training_csv).loc[:1, list(FEATURE_COLUMNS)]
    for invalid in (
        X.drop(columns=[FEATURE_COLUMNS[0]]),
        X.iloc[:0],
        pd.concat([X, X[[FEATURE_COLUMNS[0]]]], axis=1),
    ):
        with pytest.raises(ModelArtifactError, match="exactly the five"):
            prediction_features(invalid)


def test_unsupported_artifact_schema_fails_safely(tmp_path):
    path = tmp_path / "local-invalid.joblib"
    joblib.dump({"artifact_schema_version": 999}, path)
    with pytest.raises(ModelArtifactError, match="Unsupported model artifact schema"):
        load_model(path, expected_sha256=file_sha256(path), trusted=True)


def test_partial_test_run_cannot_silently_retry(training_csv, tmp_path, monkeypatch):
    original = Pipeline.predict_proba

    def interrupted(self, X, *args, **kwargs):
        if X["Order Country"].eq("Synthetic Test").any():
            raise RuntimeError("simulated interruption")
        return original(self, X, *args, **kwargs)

    monkeypatch.setattr(Pipeline, "predict_proba", interrupted)
    run = tmp_path / "interrupted"
    with pytest.raises(RuntimeError, match="simulated interruption"):
        run_training(training_csv, run)
    assert (run / "selection.json").is_file()
    assert (run / "test_evaluation.started").is_file()
    with pytest.raises(DatasetValidationError, match="Incomplete run"):
        run_training(training_csv, run)


def test_subgroups_suppress_insufficient_samples():
    X = pd.DataFrame(
        {
            column: ["Synthetic Group"] * 4
            for column in ("Shipping Mode", "Market", "Order Region")
        }
    )
    y = pd.Series([0, 1, 0, 1])
    probabilities = np.array([0.1, 0.8, 0.2, 0.9])
    hidden = subgroup_metrics(X, y, probabilities, 0.5)
    assert hidden["Market"]["groups"] == {}
    visible = subgroup_metrics(
        X, y, probabilities, 0.5, min_orders=4, min_class_orders=2
    )
    assert visible["Market"]["groups"]["Synthetic Group"]["f1"] == 1


def test_completed_artifact_corruption_is_not_retested(training_csv, tmp_path):
    run = tmp_path / "run"
    run_training(training_csv, run)
    artifact = run / "pipeline.joblib"
    checksum = file_sha256(artifact)
    artifact.write_bytes(b"corrupted")
    assert file_sha256(artifact) != checksum
    with pytest.raises(DatasetValidationError, match="checksum differs"):
        run_training(training_csv, run)
