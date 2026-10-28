"""Validation-only investigation tests use invented rows and no model fitting."""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from freightguard.diagnose_model import (
    FROZEN_FILES,
    load_train_validation,
    run_diagnostics,
    top_k_metrics,
    training_rate_scores,
    validation_diagnostics,
)
from freightguard.model_artifact import PredictionModel
from freightguard.prepare_data import OrderSplit
from freightguard.validate_data import FEATURE_COLUMNS, DatasetValidationError


class FrozenStub:
    def predict_proba(self, X):
        assert list(X.columns) == list(FEATURE_COLUMNS)
        assert X["Market"].eq("Synthetic Validation Market").all()
        p = np.where(X[FEATURE_COLUMNS[0]].eq(1), 0.9, 0.25)
        return np.column_stack([1 - p, p])

    def fit(self, *args):
        pytest.fail("Diagnostics must never fit a model")


def make_split(country, count=200):
    y = pd.Series(np.arange(count) % 2, name="Late_delivery_risk")
    X = pd.DataFrame(
        {
            FEATURE_COLUMNS[0]: np.where(y.eq(1), 1, 4),
            "Shipping Mode": "Standard Class",
            "Market": "Synthetic Validation Market",
            "Order Region": "Synthetic Region",
            "Order Country": country,
        }
    )
    return OrderSplit(
        X,
        y,
        pd.Series(np.arange(count)),
        pd.Series(pd.to_datetime(["2017-03-01"] * count)),
    )


def test_top_k_ties_use_expected_credit_and_bounds_not_row_order():
    y = pd.Series([1, 0, 1, 0])
    p = np.array([0.9, 0.9, 0.8, 0.1])
    result = top_k_metrics(y, p, 0.25)
    assert result["review_orders"] == 1
    assert result["precision_at_k"] == 0.5
    assert result["recall_at_k"] == 0.25
    assert result["lift_vs_random"] == 1
    assert result["precision_tie_lower"] == 0
    assert result["precision_tie_upper"] == 1
    permutation = [3, 1, 0, 2]
    assert top_k_metrics(y.iloc[permutation], p[permutation], 0.25) == result


def test_top_k_rounding_and_no_positive_labels():
    result = top_k_metrics(pd.Series([0, 0, 0]), np.array([0.2, 0.2, 0.1]), 0.1)
    assert result["review_orders"] == 1
    assert result["recall_at_k"] is None
    assert result["lift_vs_random"] is None
    assert top_k_metrics(pd.Series([0, 1]), np.array([0.1, 0.9]), 1)["alert_rate"] == 1


@pytest.mark.parametrize("fraction", [0, -1, 1.1, float("nan")])
def test_invalid_capacity_rejected(fraction):
    with pytest.raises(ValueError):
        top_k_metrics(pd.Series([0, 1]), np.array([0.1, 0.9]), fraction)


def test_training_frequency_reference_does_not_use_validation_labels():
    train = make_split("Synthetic Train")
    validation = make_split("Synthetic Validation")
    first = training_rate_scores(train, validation, [FEATURE_COLUMNS[0]])
    validation.y = 1 - validation.y
    second = training_rate_scores(train, validation, [FEATURE_COLUMNS[0]])
    np.testing.assert_array_equal(first, second)
    assert set(first) == {0.0, 1.0}


def test_diagnostics_preserve_threshold_and_report_within_mode():
    model = PredictionModel(FrozenStub(), 0.4, "v1")
    train, validation = make_split("Train"), make_split("Validation")
    first = validation_diagnostics(model, train, validation)
    second = validation_diagnostics(model, train, validation)
    assert first == second
    assert model.threshold == 0.4
    assert (
        first["by_shipping_mode"]["Standard Class"]["metrics_at_frozen_threshold"][
            "roc_auc"
        ]
        == 1
    )
    assert first["training_frequency_references"]["scheduled_days"][
        "model_score_variance_explained_by_group"
    ] == pytest.approx(1)
    assert (
        first["grouped_permutation_sensitivity"]["geography"]["pr_auc_drop_mean"] == 0
    )
    assert "test_metrics" not in first


def test_large_one_class_modes_are_descriptive_with_undefined_auc():
    model = PredictionModel(FrozenStub(), 0.4, "v1")
    train, validation = make_split("Train"), make_split("Validation")
    validation.X.loc[validation.y.eq(1), "Shipping Mode"] = "First Class"
    result = validation_diagnostics(model, train, validation)
    metrics = result["by_shipping_mode"]["First Class"]["metrics_at_frozen_threshold"]
    assert metrics["roc_auc"] is None and metrics["pr_auc"] is None


def test_one_class_overall_cohort_is_rejected():
    validation = make_split("Validation")
    validation.y[:] = 1
    with pytest.raises(DatasetValidationError, match="both target classes"):
        validation_diagnostics(
            PredictionModel(FrozenStub(), 0.4, "v1"), make_split("Train"), validation
        )


@pytest.fixture
def diagnostic_csv(tmp_path):
    rows = []
    for timestamp, risk, actual in (
        ("6/1/2016 12:00", 0, 4),
        ("6/2/2016 12:00", 1, 2),
        ("3/1/2017 12:00", 0, 4),
        ("3/2/2017 12:00", 1, 2),
        # Deliberately corrupt held-out outcomes: they must not be validated/used.
        ("7/1/2017 12:00", "private-invalid-target", -999),
        ("6/24/2017 12:00", "private-invalid-gap", -999),
    ):
        rows.append(
            {
                "Order Id": len(rows) + 1,
                "Order Item Id": len(rows) + 1,
                "order date (DateOrders)": timestamp,
                "Late_delivery_risk": risk,
                "Days for shipment (scheduled)": 1 if risk == 1 else 4,
                "Days for shipping (real)": actual,
                "Shipping Mode": "Standard Class",
                "Delivery Status": "Late delivery" if risk == 1 else "Shipping on time",
                "Order Status": "COMPLETE",
                "Market": "Synthetic Validation Market",
                "Order Region": "Synthetic Region",
                "Order Country": "Synthetic Country",
                "Customer Email": "private-sentinel",
            }
        )
    path = tmp_path / "synthetic.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_loader_excludes_test_and_gap_outcomes_before_validation(diagnostic_csv):
    train, validation = load_train_validation(diagnostic_csv)
    assert train.order_ids.tolist() == [1, 2]
    assert validation.order_ids.tolist() == [3, 4]
    assert validation.y.tolist() == [0, 1]


def test_runner_never_modifies_frozen_artifacts_and_output_is_reproducible(
    diagnostic_csv, tmp_path, monkeypatch
):
    root = tmp_path / "frozen"
    root.mkdir()
    (root / "pipeline.joblib").write_bytes(b"synthetic placeholder; loader is stubbed")
    model_hash = hashlib.sha256((root / "pipeline.joblib").read_bytes()).hexdigest()
    (root / "evaluation.json").write_text(
        json.dumps(
            {
                "dataset_sha256": hashlib.sha256(
                    diagnostic_csv.read_bytes()
                ).hexdigest(),
                "artifact_sha256": model_hash,
                "split_config": {
                    "validation_start": "2017-01-01",
                    "test_start": "2017-07-01",
                    "gap_days": 7,
                },
                "selected_threshold": 0.4,
                "model_version": "v1",
                "test_metrics": {"private-sentinel": "must never be returned"},
            }
        )
    )
    (root / "selection.json").write_text("{}")
    (root / "test_evaluation.started").write_text("Do not change")
    before = {name: (root / name).read_bytes() for name in FROZEN_FILES}

    def trusted_loader(path, *, expected_sha256, trusted):
        assert trusted and expected_sha256 == model_hash
        return PredictionModel(FrozenStub(), 0.4, "v1")

    monkeypatch.setattr("freightguard.diagnose_model.load_model", trusted_loader)
    output = tmp_path / "diagnostics.json"
    first = run_diagnostics(
        diagnostic_csv, root, output, expected_model_sha256=model_hash, trusted=True
    )
    second = run_diagnostics(
        diagnostic_csv, root, output, expected_model_sha256=model_hash, trusted=True
    )
    assert first == second == json.loads(output.read_text())
    assert "private-" not in output.read_text()
    assert before == {name: (root / name).read_bytes() for name in FROZEN_FILES}
