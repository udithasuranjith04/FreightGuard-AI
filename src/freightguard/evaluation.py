"""Aggregate binary-classification metrics; never retain prediction records."""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_probabilities(
    y: pd.Series, probabilities: np.ndarray, threshold: float
) -> dict:
    """PR-AUC is average precision; positive class is late (1)."""
    values = np.asarray(probabilities, dtype=float)
    if (
        len(y) == 0
        or values.shape != (len(y),)
        or not y.isin([0, 1]).all()
        or not np.isfinite(values).all()
        or (values < 0).any()
        or (values > 1).any()
        or not 0 <= threshold <= 1
    ):
        raise ValueError("Invalid evaluation inputs.")
    predicted = (values >= threshold).astype(int)
    both_classes = y.nunique() == 2
    bins = []
    for index in range(10):
        mask = (values >= index / 10) & (
            values < (index + 1) / 10 if index < 9 else values <= 1
        )
        if mask.any():
            bins.append(
                {
                    "lower": index / 10,
                    "upper": (index + 1) / 10,
                    "orders": int(mask.sum()),
                    "mean_probability": float(values[mask].mean()),
                    "observed_late_rate": float(y.to_numpy()[mask].mean()),
                }
            )
    return {
        "orders": len(y),
        "threshold": float(threshold),
        "late_rate": float(y.mean()),
        "accuracy": float(accuracy_score(y, predicted)),
        "precision": float(precision_score(y, predicted, zero_division=0)),
        "recall": float(recall_score(y, predicted, zero_division=0)),
        "f1": float(f1_score(y, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, values)) if both_classes else None,
        "pr_auc": float(average_precision_score(y, values)) if both_classes else None,
        "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
        "brier_score": float(brier_score_loss(y, values)),
        "log_loss": float(
            log_loss(y, np.column_stack([1 - values, values]), labels=[0, 1])
        ),
        "calibration_bins": bins,
        "expected_calibration_error": sum(
            row["orders"]
            / len(y)
            * abs(row["mean_probability"] - row["observed_late_rate"])
            for row in bins
        ),
    }


def subgroup_metrics(
    X: pd.DataFrame,
    y: pd.Series,
    probabilities: np.ndarray,
    threshold: float,
    min_orders: int = 100,
    min_class_orders: int = 10,
) -> dict:
    """Suppress small/one-class groups; group labels are approved broad fields."""
    report = {}
    for column in ("Shipping Mode", "Market", "Order Region"):
        groups = {}
        suppressed = 0
        for value in sorted(X[column].unique()):
            mask = X[column].eq(value).to_numpy()
            labels = y.loc[mask]
            if (
                len(labels) < min_orders
                or min(int(labels.eq(0).sum()), int(labels.eq(1).sum()))
                < min_class_orders
            ):
                suppressed += 1
                continue
            groups[value] = evaluate_probabilities(
                labels, probabilities[mask], threshold
            )
        report[column] = {"groups": groups, "suppressed_groups": suppressed}
    return report
