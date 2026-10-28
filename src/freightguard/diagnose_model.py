"""Exploratory validation-only diagnostics for an explicitly trusted frozen model."""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from freightguard.evaluation import evaluate_probabilities
from freightguard.model_artifact import ModelArtifactError, PredictionModel, load_model
from freightguard.prepare_data import OrderSplit, SplitConfig, save_metadata
from freightguard.train_model import DEFAULT_RUN_DIR, file_sha256
from freightguard.validate_data import (
    DEFAULT_DATA_PATH,
    FEATURE_COLUMNS,
    ORDER_DATE,
    ORDER_ID,
    TARGET,
    DatasetValidationError,
    eligible_orders,
    load_dataset,
)

CAPACITIES = (0.05, 0.10, 0.20, 0.30, 0.50)
SEED = 42
DEFAULT_OUTPUT = (
    DEFAULT_DATA_PATH.parents[1] / "processed/diagnostics/v1_validation.json"
)
FROZEN_FILES = (
    "evaluation.json",
    "selection.json",
    "pipeline.joblib",
    "test_evaluation.started",
)


def top_k_metrics(y: pd.Series, scores: np.ndarray, fraction: float) -> dict:
    """Expected performance with uniform tie-breaking, plus boundary-tie bounds.

    No order IDs, row order, or labels decide which tied records get reviewed.
    This computes aggregates, not an actual queue or a new prediction threshold.
    """
    # Reuse strict binary/probability validation, including shape checks.
    evaluate_probabilities(y, scores, 0.5)
    if not 0 < fraction <= 1:
        raise ValueError("Review fraction must be in (0, 1].")
    scores = np.asarray(scores)
    count = min(len(y), math.ceil(len(y) * fraction))
    cutoff = float(np.sort(scores)[-count])
    above = scores > cutoff
    tied = scores == cutoff
    remaining = count - int(above.sum())
    positives_above = int(y.to_numpy()[above].sum())
    positives_tied = int(y.to_numpy()[tied].sum())
    tie_count = int(tied.sum())
    expected = positives_above + remaining * positives_tied / tie_count
    positives = int(y.sum())
    low = positives_above + max(0, remaining - (tie_count - positives_tied))
    high = positives_above + min(remaining, positives_tied)
    return {
        "requested_fraction": fraction,
        "review_orders": count,
        "alert_rate": count / len(y),
        "boundary_score": cutoff,
        "boundary_tied_orders": tie_count,
        "boundary_slots": remaining,
        "expected_late_reviewed": expected,
        "precision_at_k": expected / count,
        "recall_at_k": expected / positives if positives else None,
        "lift_vs_random": expected / count / y.mean() if positives else None,
        "precision_tie_lower": low / count,
        "precision_tie_upper": high / count,
    }


def _quantiles(values: np.ndarray) -> dict | None:
    if len(values) == 0:
        return None
    return {
        str(q): float(np.quantile(values, q)) for q in (0, 0.1, 0.25, 0.5, 0.75, 0.9, 1)
    }


def score_diagnostics(y: pd.Series, scores: np.ndarray, threshold: float) -> dict:
    metrics = evaluate_probabilities(y, scores, threshold)
    tn, fp = metrics["confusion_matrix"][0]
    fn, tp = metrics["confusion_matrix"][1]
    return {
        "metrics_at_frozen_threshold": metrics,
        "score_quantiles": _quantiles(scores),
        "score_quantiles_by_class": {
            str(label): _quantiles(scores[y.eq(label).to_numpy()]) for label in (0, 1)
        },
        "alert_rate": (fp + tp) / len(y),
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "false_negative_rate": fn / (fn + tp) if fn + tp else None,
        "capacity_policies": [
            top_k_metrics(y, scores, fraction) for fraction in CAPACITIES
        ],
    }


def training_rate_scores(
    train: OrderSplit, validation: OrderSplit, columns: list[str]
) -> np.ndarray:
    """Descriptive frequency reference calculated only from training outcomes."""
    grouped = train.X.loc[:, columns].copy()
    grouped["_label"] = train.y.to_numpy()
    rates = grouped.groupby(columns)["_label"].mean().to_dict()
    prior = float(train.y.mean())
    return np.array(
        [
            rates.get(row[0] if len(columns) == 1 else row, prior)
            for row in validation.X.loc[:, columns].itertuples(index=False, name=None)
        ]
    )


def _score_variance_explained(
    X: pd.DataFrame, scores: np.ndarray, columns: list[str]
) -> float | None:
    total = float(np.sum((scores - scores.mean()) ** 2))
    if total == 0:
        return None
    frame = X.loc[:, columns].copy()
    frame["_score"] = scores
    means = frame.groupby(columns)["_score"].transform("mean").to_numpy()
    return float(1 - np.sum((scores - means) ** 2) / total)


def validation_diagnostics(
    model: PredictionModel, train: OrderSplit, validation: OrderSplit
) -> dict:
    """Only train/validation are accepted; no fitting, test input, or artifact edits."""
    if validation.y.nunique() != 2:
        raise DatasetValidationError(
            "Validation diagnostics require both target classes."
        )
    scores = model.predict(validation.X)["late_probability"].to_numpy()
    y = validation.y
    overall = score_diagnostics(y, scores, model.threshold)
    by_mode = {}
    suppressed = 0
    for mode in sorted(validation.X["Shipping Mode"].unique()):
        mask = validation.X["Shipping Mode"].eq(mode).to_numpy()
        if int(mask.sum()) < 100:
            suppressed += 1
            continue
        # Large one-class groups remain descriptive: AUC is null, never invented.
        by_mode[mode] = score_diagnostics(y.loc[mask], scores[mask], model.threshold)
    references = {}
    for name, columns in (
        ("shipping_mode", ["Shipping Mode"]),
        ("scheduled_days", [FEATURE_COLUMNS[0]]),
        ("shipping_plan", ["Shipping Mode", FEATURE_COLUMNS[0]]),
    ):
        values = training_rate_scores(train, validation, columns)
        references[name] = {
            "metrics": evaluate_probabilities(y, values, 0.5),
            "capacity_policies": [top_k_metrics(y, values, f) for f in CAPACITIES],
            "model_score_variance_explained_by_group": _score_variance_explained(
                validation.X, scores, columns
            ),
        }
    base = overall["metrics_at_frozen_threshold"]
    permutation = {}
    for name, columns in (
        ("shipping_plan", [FEATURE_COLUMNS[0], "Shipping Mode"]),
        ("geography", list(FEATURE_COLUMNS[2:])),
    ):
        drops = []
        for repeat in range(5):
            rng = np.random.default_rng(SEED + repeat)
            order = rng.permutation(len(y))
            shuffled = validation.X.copy()
            shuffled.loc[:, columns] = validation.X.iloc[order][columns].to_numpy()
            probabilities = model.predict(shuffled)["late_probability"].to_numpy()
            perturbed = evaluate_probabilities(y, probabilities, model.threshold)
            drops.append(base["pr_auc"] - perturbed["pr_auc"])
        permutation[name] = {
            "pr_auc_drop_mean": float(np.mean(drops)),
            "pr_auc_drop_std": float(np.std(drops)),
            "repeats": len(drops),
        }
    tradeoffs = []
    for threshold in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
        metric = evaluate_probabilities(y, scores, threshold)
        _tn, fp = metric["confusion_matrix"][0]
        fn, tp = metric["confusion_matrix"][1]
        tradeoffs.append(
            {
                **{
                    key: metric[key]
                    for key in ("threshold", "precision", "recall", "f1")
                },
                "alert_rate": (fp + tp) / len(y),
                "false_alarms": fp,
                "missed_late": fn,
            }
        )
    return {
        "diagnostics_version": 1,
        "scope": "exploratory validation only; no new test evaluation",
        "model_version": model.model_version,
        "frozen_threshold": model.threshold,
        "random_seed": SEED,
        "validation_orders": len(y),
        "training_reference_orders": len(train.y),
        "overall": overall,
        "by_shipping_mode": by_mode,
        "suppressed_small_shipping_modes": suppressed,
        "training_frequency_references": references,
        "grouped_permutation_sensitivity": permutation,
        "exploratory_threshold_tradeoffs": tradeoffs,
        "tie_policy": "uniform expected selection at boundary; capacity rounded up",
        "policy_status": "proposal only; no threshold or deployment policy changed",
        "versions": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
        },
    }


def load_train_validation(path: Path) -> tuple[OrderSplit, OrderSplit]:
    """Discard the test period before validating labels or constructing diagnostics.

    The CSV parser reads approved columns, but later rows are discarded by date;
    their targets never reach eligibility checks, references, or model prediction.
    """
    config = SplitConfig()
    validation_start, test_start, gap = config.boundaries()
    frame = load_dataset(path)
    dates = pd.to_datetime(frame[ORDER_DATE], format="%m/%d/%Y %H:%M", errors="coerce")
    if dates.isna().any():
        raise DatasetValidationError("Invalid order dates in source snapshot.")
    earlier = frame.loc[dates.lt(test_start - gap)].copy()
    orders = eligible_orders(earlier)
    result = []
    for mask in (
        orders[ORDER_DATE].lt(validation_start - gap),
        orders[ORDER_DATE].ge(validation_start),
    ):
        part = orders.loc[mask].reset_index(drop=True)
        if part.empty or part[TARGET].nunique() != 2:
            raise DatasetValidationError(
                "Train/validation diagnostic cohort is invalid."
            )
        result.append(
            OrderSplit(
                part.loc[:, list(FEATURE_COLUMNS)].copy(),
                part[TARGET].astype("int64"),
                part[ORDER_ID].copy(),
                part[ORDER_DATE].copy(),
            )
        )
    return result[0], result[1]


def run_diagnostics(
    data_path: Path,
    model_dir: Path,
    output: Path,
    *,
    expected_model_sha256: str,
    trusted: bool = False,
) -> dict:
    frozen_hashes = {name: file_sha256(model_dir / name) for name in FROZEN_FILES}
    frozen = json.loads((model_dir / "evaluation.json").read_text())
    data_hash = file_sha256(data_path)
    if (
        data_hash != frozen["dataset_sha256"]
        or frozen["artifact_sha256"] != expected_model_sha256
        or frozen["split_config"]
        != {"validation_start": "2017-01-01", "test_start": "2017-07-01", "gap_days": 7}
    ):
        raise DatasetValidationError(
            "Frozen artifact, dataset, or split identity differs."
        )
    model = load_model(
        model_dir / "pipeline.joblib",
        expected_sha256=expected_model_sha256,
        trusted=trusted,
    )
    if (
        model.threshold != frozen["selected_threshold"]
        or model.model_version != frozen["model_version"]
    ):
        raise DatasetValidationError("Frozen model version or threshold differs.")
    train, validation = load_train_validation(data_path)
    report = validation_diagnostics(model, train, validation)
    report["dataset_sha256"] = data_hash
    report["frozen_artifact_hashes"] = frozen_hashes
    if frozen_hashes != {name: file_sha256(model_dir / name) for name in FROZEN_FILES}:
        raise DatasetValidationError("Frozen artifacts changed during diagnostics.")
    save_metadata(report, output)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-model-sha256", required=True)
    parser.add_argument("--trust-local-model", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = run_diagnostics(
            args.data,
            args.model_dir,
            args.output,
            expected_model_sha256=args.expected_model_sha256,
            trusted=args.trust_local_model,
        )
    except (DatasetValidationError, ModelArtifactError) as error:
        print(f"Diagnostics stopped: {error}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError, KeyError):
        print(
            "Diagnostics stopped: cannot read local inputs or save metadata.",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
