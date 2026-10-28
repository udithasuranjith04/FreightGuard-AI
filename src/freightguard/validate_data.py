"""Validate the local DataCo delivery-delay contract without exposing records."""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[2] / "data/raw/DataCoSupplyChainDataset.csv"
)
TARGET = "Late_delivery_risk"
ORDER_ID = "Order Id"
ITEM_ID = "Order Item Id"
ORDER_DATE = "order date (DateOrders)"
DATE_FORMAT = "%m/%d/%Y %H:%M"

# Only these five fields are eligible prediction inputs for the baseline.
FEATURE_COLUMNS = (
    "Days for shipment (scheduled)",
    "Shipping Mode",
    "Market",
    "Order Region",
    "Order Country",
)
# Audit metadata and outcomes must never be added to the feature allowlist.
AUDIT_COLUMNS = (
    ORDER_ID,
    ITEM_ID,
    ORDER_DATE,
    TARGET,
    "Delivery Status",
    "Order Status",
    "Days for shipping (real)",
)
REQUIRED_COLUMNS = FEATURE_COLUMNS + AUDIT_COLUMNS
DELIVERY_STATUSES = (
    "Advance shipping",
    "Late delivery",
    "Shipping canceled",
    "Shipping on time",
)
ORDER_STATUSES = (
    "CANCELED",
    "CLOSED",
    "COMPLETE",
    "ON_HOLD",
    "PAYMENT_REVIEW",
    "PENDING",
    "PENDING_PAYMENT",
    "PROCESSING",
    "SUSPECTED_FRAUD",
)
SHIPPING_MODES = ("First Class", "Second Class", "Standard Class", "Same Day")


class DatasetValidationError(ValueError):
    """A contract violation whose message contains no dataset values."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DatasetValidationError(message)


def load_dataset(path: Path) -> pd.DataFrame:
    """Read only approved audit columns, never customer fields."""
    try:
        with path.open(encoding="latin-1", newline="") as stream:
            header = next(csv.reader(stream), [])
        _require(len(header) == len(set(header)), "Duplicate column names found.")
        _require(
            set(REQUIRED_COLUMNS).issubset(header),
            "Dataset is missing required validation columns.",
        )
        return pd.read_csv(
            path,
            encoding="latin-1",
            usecols=list(REQUIRED_COLUMNS),
            low_memory=False,
        ).loc[:, list(REQUIRED_COLUMNS)]
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError, csv.Error):
        # Parser exceptions may contain row contents or local paths.
        raise DatasetValidationError(
            "Cannot read dataset; check the local CSV path and format."
        ) from None


def _validated_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate types and domains on a copy containing only known columns."""
    _require(frame.columns.is_unique, "Duplicate column names found.")
    _require(
        set(REQUIRED_COLUMNS).issubset(frame.columns),
        "Dataset is missing required validation columns.",
    )
    _require(not frame.empty, "Dataset contains no rows.")
    data = frame.loc[:, list(REQUIRED_COLUMNS)].copy()
    _require(not data.isna().any().any(), "Required validation fields contain nulls.")

    numeric_columns = (
        ORDER_ID,
        ITEM_ID,
        TARGET,
        "Days for shipment (scheduled)",
        "Days for shipping (real)",
    )
    for column in numeric_columns:
        values = pd.to_numeric(data[column], errors="coerce")
        _require(
            bool(
                (
                    values.notna()
                    & np.isfinite(values)
                    & values.ge(0)
                    & values.mod(1).eq(0)
                ).all()
            ),
            f"Invalid nonnegative integer field: {column}.",
        )
        data[column] = values
    _require(data[TARGET].isin([0, 1]).all(), "Target must contain only 0 or 1.")
    for column in (ORDER_ID, ITEM_ID):
        _require(data[column].gt(0).all(), f"Identifiers must be positive: {column}.")
    _require(data[ITEM_ID].is_unique, "Duplicate order item identifiers found.")

    for column in FEATURE_COLUMNS[1:]:
        _require(
            data[column]
            .map(lambda value: isinstance(value, str) and bool(value.strip()))
            .all(),
            f"Invalid or blank text field: {column}.",
        )
    for column, allowed in (
        ("Delivery Status", DELIVERY_STATUSES),
        ("Order Status", ORDER_STATUSES),
        ("Shipping Mode", SHIPPING_MODES),
    ):
        _require(data[column].isin(allowed).all(), f"Unexpected category: {column}.")

    dates = pd.to_datetime(data[ORDER_DATE], format=DATE_FORMAT, errors="coerce")
    _require(dates.notna().all(), "Invalid order dates; expected month/day/year time.")
    data[ORDER_DATE] = dates
    order_fields = list(FEATURE_COLUMNS) + [
        ORDER_DATE,
        TARGET,
        "Delivery Status",
        "Order Status",
        "Days for shipping (real)",
    ]
    _require(
        not data.groupby(ORDER_ID)[order_fields].nunique().gt(1).any().any(),
        "Items in an order disagree on order-level fields or outcomes.",
    )
    return data


def _canceled(data: pd.DataFrame) -> pd.Series:
    return data["Delivery Status"].eq("Shipping canceled") | data["Order Status"].isin(
        ["CANCELED", "SUSPECTED_FRAUD"]
    )


def _target_counts(data: pd.DataFrame) -> dict[str, int]:
    return {str(label): int(data[TARGET].eq(label).sum()) for label in (0, 1)}


def _eligible_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Check outcome consistency before excluding canceled observations."""
    canceled = _canceled(data)
    _require(
        data["Delivery Status"]
        .eq("Shipping canceled")
        .equals(data["Order Status"].isin(["CANCELED", "SUSPECTED_FRAUD"])),
        "Cancellation indicators disagree.",
    )
    _require(
        data[TARGET].eq(1).equals(data["Delivery Status"].eq("Late delivery")),
        "Delivery status and target disagree.",
    )
    eligible = data.loc[~canceled]
    _require(not eligible.empty, "No non-canceled orders remain.")
    duration_late = eligible["Days for shipping (real)"].gt(
        eligible["Days for shipment (scheduled)"]
    )
    _require(
        duration_late.equals(eligible[TARGET].eq(1)),
        "Non-canceled duration rule and target disagree.",
    )
    return eligible


def validate_dataset(frame: pd.DataFrame) -> dict:
    """Return deterministic aggregate evidence; fail closed on contract drift.

    Extra columns are ignored, never returned. Raw input is not modified.
    Counts distinguish item rows from orders to avoid overstating sample size.
    """
    data = _validated_frame(frame)
    canceled = _canceled(data)
    eligible = _eligible_rows(data)
    orders = data.drop_duplicates(ORDER_ID)
    eligible_orders = eligible.drop_duplicates(ORDER_ID)
    return {
        "contract_version": 1,
        "rows": len(data),
        "orders": len(orders),
        "multi_item_orders": int(data.groupby(ORDER_ID).size().gt(1).sum()),
        "repeated_order_rows": int(data[ORDER_ID].duplicated().sum()),
        "duplicate_item_ids": 0,
        "missing_required": {column: 0 for column in REQUIRED_COLUMNS},
        "raw_item_target_counts": _target_counts(data),
        "excluded_canceled_rows": int(canceled.sum()),
        "excluded_canceled_orders": int(orders.loc[_canceled(orders)].shape[0]),
        "eligible_rows": len(eligible),
        "eligible_orders": len(eligible_orders),
        "eligible_item_target_counts": _target_counts(eligible),
        "eligible_order_target_counts": _target_counts(eligible_orders),
        "order_date_min": data[ORDER_DATE].min().isoformat(),
        "order_date_max": data[ORDER_DATE].max().isoformat(),
        "delivery_status_reveals_target": True,
        "eligible_duration_rule_matches_target": True,
        "feature_columns": list(FEATURE_COLUMNS),
    }


def order_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Select one row per eligible order with only the five allowed inputs.

    This is contract selection, not fitted preprocessing or a training pipeline.
    The output index is reset so identifiers do not accidentally become features.
    """
    orders = _eligible_rows(_validated_frame(frame)).drop_duplicates(ORDER_ID)
    return orders.loc[:, list(FEATURE_COLUMNS)].reset_index(drop=True).copy()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    args = parser.parse_args(argv)
    try:
        report = validate_dataset(load_dataset(args.data))
        digest = hashlib.sha256()
        with args.data.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        report["dataset_sha256"] = digest.hexdigest()
    except (DatasetValidationError, OSError) as error:
        message = (
            str(error)
            if isinstance(error, DatasetValidationError)
            else ("Cannot read dataset fingerprint.")
        )
        print(f"Validation failed: {message}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
