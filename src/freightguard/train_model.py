"""Select on validation only, freeze, and evaluate the selected model on test once."""

import argparse
import hashlib
import json
import logging
import platform
import re
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

from freightguard.evaluation import evaluate_probabilities, subgroup_metrics
from freightguard.prepare_data import (
    OrderSplit,
    build_preprocessor,
    chronological_splits,
)
from freightguard.validate_data import (
    DEFAULT_DATA_PATH,
    FEATURE_COLUMNS,
    DatasetValidationError,
    load_dataset,
)

LOGGER = logging.getLogger(__name__)
SEED = 42
DEFAULT_RUN_DIR = DEFAULT_DATA_PATH.parents[1] / "processed/models/v1"
THRESHOLDS = tuple(round(float(value), 2) for value in np.arange(0.05, 1, 0.05))
SELECTION_RULE = (
    "Maximize validation F1 over thresholds 0.05..0.95 step 0.05; threshold ties: "
    "closest to 0.50, then lower threshold. Model ties: higher validation average "
    "precision (PR-AUC), then simpler candidate (dummy, logistic, forest)."
)


@dataclass
class Selection:
    pipeline: Pipeline
    name: str
    threshold: float
    report: dict


def candidates() -> dict:
    """Fixed small search, seeded and single-worker; no test-dependent parameters."""
    return {
        "dummy_majority": DummyClassifier(strategy="most_frequent", random_state=SEED),
        "logistic_regression": LogisticRegression(
            C=1.0, solver="liblinear", max_iter=1000, random_state=SEED
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_leaf=20,
            random_state=SEED,
            n_jobs=1,
        ),
    }


def select_model(train: OrderSplit, validation: OrderSplit) -> Selection:
    """No test parameter exists: only train/validation can influence selection."""
    reports = {}
    best = None
    best_key = None
    for rank, (name, classifier) in enumerate(candidates().items()):
        LOGGER.info("Fitting candidate: %s", name)
        pipeline = Pipeline(
            [("preprocessor", build_preprocessor()), ("classifier", classifier)]
        )
        pipeline.fit(train.X, train.y)
        probabilities = pipeline.predict_proba(validation.X)[:, 1]
        threshold = max(
            THRESHOLDS,
            key=lambda value: (
                f1_score(validation.y, probabilities >= value, zero_division=0),
                -abs(value - 0.5),
                -value,
            ),
        )
        tuned = evaluate_probabilities(validation.y, probabilities, threshold)
        reports[name] = {
            "parameters": classifier.get_params(deep=False),
            "explanation": model_explanation(pipeline),
            "at_0_50": evaluate_probabilities(validation.y, probabilities, 0.5),
            "selected_threshold_metrics": tuned,
        }
        key = (tuned["f1"], tuned["pr_auc"], -rank)
        if best_key is None or key > best_key:
            best_key = key
            best = (pipeline, name, threshold)
    pipeline, name, threshold = best
    report = {
        "selection_rule": SELECTION_RULE,
        "random_seed": SEED,
        "selected_model": name,
        "selected_threshold": threshold,
        "validation_candidates": reports,
        "training_class_counts": {
            str(label): int(train.y.eq(label).sum()) for label in (0, 1)
        },
        "training_orders": len(train.y),
        "validation_orders": len(validation.y),
        "training_prior_probability": float(train.y.mean()),
        "validation_prior_brier_score": float(
            ((validation.y - train.y.mean()) ** 2).mean()
        ),
        "fitted_on": "training only; no train+validation refit",
    }
    return Selection(pipeline, name, threshold, report)


def model_explanation(pipeline: Pipeline) -> dict:
    """Aggregate feature importance/coefficients, not individual explanations."""
    classifier = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]
    if hasattr(classifier, "coef_"):
        names = preprocessor.get_feature_names_out()
        values = classifier.coef_[0]
        top = np.argsort(-np.abs(values), kind="stable")[:10]
        return {
            "kind": "logistic_coefficients",
            "largest_absolute_coefficients": [
                {"feature": str(names[index]), "coefficient": float(values[index])}
                for index in top
            ],
        }
    if hasattr(classifier, "feature_importances_"):
        values = classifier.feature_importances_
        sizes = [1] + [
            len(group)
            for group in preprocessor.named_transformers_["categorical"].categories_
        ]
        result = {}
        offset = 0
        for column, size in zip(FEATURE_COLUMNS, sizes):
            result[column] = float(values[offset : offset + size].sum())
            offset += size
        return {"kind": "forest_impurity_importance", "by_input": result}
    return {"kind": "constant_majority_prediction"}


def _write_json(path: Path, payload: dict) -> None:
    with path.open("x") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_training(data_path: Path, run_dir: Path, model_version: str = "v1") -> dict:
    """Immutable run directory: repeat calls replay JSON, never retest or unpickle.

    A partial run fails closed and must be inspected manually, not auto-retried.
    The test marker is created before prediction, so failure cannot silently retry.
    """
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", model_version):
        raise DatasetValidationError("Invalid model version.")
    fingerprint = file_sha256(data_path)
    report_path = run_dir / "evaluation.json"
    if run_dir.exists():
        if not report_path.is_file():
            raise DatasetValidationError(
                "Incomplete run exists; inspect it before proceeding."
            )
        try:
            report = json.loads(report_path.read_text())
            matches = (
                report["dataset_sha256"] == fingerprint
                and report["model_version"] == model_version
                and file_sha256(run_dir / "pipeline.joblib")
                == report["artifact_sha256"]
            )
        except (ValueError, KeyError, TypeError):
            raise DatasetValidationError(
                "Existing evaluation metadata is invalid."
            ) from None
        if not matches:
            raise DatasetValidationError("Existing run identity or checksum differs.")
        LOGGER.info("Replaying completed evaluation; test is not evaluated again.")
        return report
    splits, gap_orders = chronological_splits(load_dataset(data_path))
    # Reserve before training. Never overwrite a run or its final test result.
    run_dir.mkdir(parents=True, exist_ok=False)
    selection = select_model(splits["train"], splits["validation"])
    _write_json(run_dir / "selection.json", selection.report)
    payload = {
        "artifact_schema_version": 1,
        "sklearn_version": sklearn.__version__,
        "model_version": model_version,
        "feature_columns": list(FEATURE_COLUMNS),
        "threshold": selection.threshold,
        "pipeline": selection.pipeline,
    }
    artifact = run_dir / "pipeline.joblib"
    joblib.dump(payload, artifact, compress=3)
    # Single final prediction call: reuse this vector for every aggregate/test group.
    with (run_dir / "test_evaluation.started").open("x") as marker:
        marker.write("Selection frozen; do not rerun final test evaluation.\n")
    LOGGER.info("Selection frozen; evaluating the selected model on test once.")
    test = splits["test"]
    test_probabilities = selection.pipeline.predict_proba(test.X)[:, 1]
    report = {
        **selection.report,
        "artifact_schema_version": 1,
        "training_version": 1,
        "preparation_version": 1,
        "dataset_contract_version": 1,
        "model_version": model_version,
        "dataset_sha256": fingerprint,
        "artifact_sha256": file_sha256(artifact),
        "feature_columns": list(FEATURE_COLUMNS),
        "split_config": {
            "validation_start": "2017-01-01",
            "test_start": "2017-07-01",
            "gap_days": 7,
        },
        "excluded_gap_orders": gap_orders,
        "test_evaluation_count": 1,
        "test_metrics": evaluate_probabilities(
            test.y, test_probabilities, selection.threshold
        ),
        "test_subgroups": subgroup_metrics(
            test.X, test.y, test_probabilities, selection.threshold
        ),
        "subgroup_policy": {"min_orders": 100, "min_each_class": 10},
        "model_explanation": model_explanation(selection.pipeline),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
            "scipy": scipy.__version__,
            "joblib": joblib.__version__,
        },
    }
    _write_json(report_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--model-version", default="v1")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        report = run_training(args.data, args.run_dir, args.model_version)
    except DatasetValidationError as error:
        LOGGER.error("Training stopped: %s", error)
        return 1
    except OSError:
        LOGGER.error("Training stopped: cannot read data or write local artifacts.")
        return 1
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
