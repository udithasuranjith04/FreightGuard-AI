"""Prepare chronological order splits and training-only transforms; train no model."""

import argparse
import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.sparse import csr_matrix
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

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

DEFAULT_METADATA_PATH = (
    DEFAULT_DATA_PATH.parents[1] / "processed/preparation_metadata.json"
)


@dataclass(frozen=True)
class SplitConfig:
    validation_start: str = "2017-01-01"
    test_start: str = "2017-07-01"
    gap_days: int = 7

    def boundaries(self) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timedelta]:
        try:
            validation = pd.Timestamp(date.fromisoformat(self.validation_start))
            test = pd.Timestamp(date.fromisoformat(self.test_start))
        except (ValueError, TypeError):
            raise DatasetValidationError("Split dates must use YYYY-MM-DD.") from None
        if (
            validation >= test
            or not isinstance(self.gap_days, int)
            or self.gap_days < 1
        ):
            raise DatasetValidationError("Split boundaries or gap are invalid.")
        gap = pd.Timedelta(days=self.gap_days)
        if validation >= test - gap:
            raise DatasetValidationError("Gap leaves no validation interval.")
        return validation, test, gap


@dataclass
class OrderSplit:
    X: pd.DataFrame
    y: pd.Series
    order_ids: pd.Series
    dates: pd.Series


@dataclass
class PreparedData:
    splits: dict[str, OrderSplit]
    preprocessor: ColumnTransformer
    matrices: dict[str, csr_matrix]
    metadata: dict


def chronological_splits(
    frame: pd.DataFrame, config: SplitConfig | None = None
) -> tuple[dict[str, OrderSplit], int]:
    """Validate, collapse items, then split by date with no shuffling or stratifying."""
    config = config or SplitConfig()
    validation, test, gap = config.boundaries()
    orders = eligible_orders(frame)
    # This field is used only for a conservative maturity audit, never as input.
    duration = pd.to_numeric(frame["Days for shipping (real)"], errors="coerce")
    if duration.max() >= config.gap_days:
        raise DatasetValidationError("Gap must exceed observed shipping duration.")
    dates = orders[ORDER_DATE]
    masks = {
        "train": dates.lt(validation - gap),
        "validation": dates.ge(validation) & dates.lt(test - gap),
        "test": dates.ge(test),
    }
    splits = {}
    for name, mask in masks.items():
        part = orders.loc[mask].reset_index(drop=True)
        if part.empty:
            raise DatasetValidationError("A chronological split is empty.")
        if part[TARGET].nunique() != 2:
            raise DatasetValidationError("Each split must contain both target classes.")
        splits[name] = OrderSplit(
            X=part.loc[:, list(FEATURE_COLUMNS)].copy(),
            y=part[TARGET].astype("int64").copy(),
            order_ids=part[ORDER_ID].copy(),
            dates=part[ORDER_DATE].copy(),
        )
    # Defensive assertions: timestamp masks and unique-order selection must agree.
    all_ids = pd.concat([part.order_ids for part in splits.values()], ignore_index=True)
    if not all_ids.is_unique:
        raise DatasetValidationError("Order overlap found between splits.")
    return splits, len(orders) - len(all_ids)


def build_preprocessor() -> ColumnTransformer:
    """Scale scheduled days; one-hot encode geography/mode without target encoding.

    No imputation: the version 1 contract rejects missing required inputs.
    Unknown categories encode as zeros for that field; the other fields still work.
    """
    return ColumnTransformer(
        transformers=[
            ("scheduled_days", StandardScaler(), [FEATURE_COLUMNS[0]]),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
                list(FEATURE_COLUMNS[1:]),
            ),
        ],
        remainder="drop",
        sparse_threshold=1.0,
    )


def prepare_dataset(
    frame: pd.DataFrame, config: SplitConfig | None = None
) -> PreparedData:
    """Fit preprocessing on X_train only and transform held-out features in memory."""
    config = config or SplitConfig()
    splits, excluded = chronological_splits(frame, config)
    preprocessor = build_preprocessor()
    matrices = {"train": csr_matrix(preprocessor.fit_transform(splits["train"].X))}
    for name in ("validation", "test"):
        matrices[name] = csr_matrix(preprocessor.transform(splits[name].X))
    encoder = preprocessor.named_transformers_["categorical"]
    summary = {}
    for name, part in splits.items():
        if not np.isfinite(matrices[name].data).all():
            raise DatasetValidationError("Preprocessing produced non-finite values.")
        summary[name] = {
            "orders": len(part.y),
            "target_counts": {
                str(label): int(part.y.eq(label).sum()) for label in (0, 1)
            },
            "date_min": part.dates.min().isoformat(),
            "date_max": part.dates.max().isoformat(),
            "transformed_columns": matrices[name].shape[1],
            "unknown_category_rows": {
                column: int((~part.X[column].isin(categories)).sum())
                for column, categories in zip(FEATURE_COLUMNS[1:], encoder.categories_)
            },
        }
    metadata = {
        "preparation_version": 1,
        "dataset_contract_version": 1,
        "config": asdict(config),
        "split_policy": "chronological; half-open intervals; earlier-side maturity gaps",
        "order_sort": [ORDER_DATE, ORDER_ID],
        "random_seed": None,
        "feature_columns": list(FEATURE_COLUMNS),
        "target": TARGET,
        "preprocessing_fit_split": "train",
        "numeric_transform": "StandardScaler",
        "categorical_transform": "OneHotEncoder(handle_unknown=ignore)",
        "excluded_gap_orders": excluded,
        "splits": summary,
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit-learn": sklearn.__version__,
        },
    }
    return PreparedData(splits, preprocessor, matrices, metadata)


def save_metadata(metadata: dict, path: Path) -> None:
    """Save only aggregate JSON; refuse to overwrite different existing content."""
    content = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text() != content:
            raise DatasetValidationError(
                "Metadata output already differs; choose a new output path."
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_METADATA_PATH)
    parser.add_argument("--validation-start", default="2017-01-01")
    parser.add_argument("--test-start", default="2017-07-01")
    parser.add_argument("--gap-days", type=int, default=7)
    args = parser.parse_args(argv)
    try:
        prepared = prepare_dataset(
            load_dataset(args.data),
            SplitConfig(args.validation_start, args.test_start, args.gap_days),
        )
        digest = hashlib.sha256()
        with args.data.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        prepared.metadata["dataset_sha256"] = digest.hexdigest()
        save_metadata(prepared.metadata, args.output)
    except DatasetValidationError as error:
        print(f"Preparation failed: {error}", file=sys.stderr)
        return 1
    except OSError:
        print(
            "Preparation failed: cannot read input or write metadata.", file=sys.stderr
        )
        return 1
    print(json.dumps(prepared.metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
