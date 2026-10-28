"""Contract tests use invented data and never require the DataCo CSV."""

import json

import pandas as pd
import pytest

from freightguard.validate_data import (
    FEATURE_COLUMNS,
    REQUIRED_COLUMNS,
    DatasetValidationError,
    load_dataset,
    main,
    order_features,
    validate_dataset,
)


@pytest.fixture
def frame():
    rows = []
    for item, order, status, risk, actual, order_status in (
        (1, 10, "Late delivery", 1, 5, "COMPLETE"),
        (2, 10, "Late delivery", 1, 5, "COMPLETE"),
        (3, 20, "Shipping on time", 0, 4, "COMPLETE"),
        (4, 30, "Shipping canceled", 0, 6, "CANCELED"),
        (5, 40, "Shipping canceled", 0, 6, "SUSPECTED_FRAUD"),
    ):
        rows.append(
            {
                "Order Id": order,
                "Order Item Id": item,
                "order date (DateOrders)": "1/1/2017 12:00",
                "Late_delivery_risk": risk,
                "Delivery Status": status,
                "Order Status": order_status,
                "Days for shipping (real)": actual,
                "Days for shipment (scheduled)": 4,
                "Shipping Mode": "Standard Class",
                "Market": "Synthetic Market",
                "Order Region": "Synthetic Region",
                "Order Country": "Synthetic Country",
            }
        )
    return pd.DataFrame(rows)


def test_report_distinguishes_items_orders_and_cancellations(frame):
    original = frame.copy(deep=True)
    report = validate_dataset(frame)
    assert report["rows"] == 5
    assert report["orders"] == 4
    assert report["multi_item_orders"] == 1
    assert report["repeated_order_rows"] == 1
    assert report["excluded_canceled_rows"] == 2
    assert report["eligible_item_target_counts"] == {"0": 1, "1": 2}
    assert report["eligible_order_target_counts"] == {"0": 1, "1": 1}
    assert validate_dataset(frame) == report
    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("Late_delivery_risk", 2, "Target must"),
        ("Late_delivery_risk", None, "contain nulls"),
        ("Days for shipment (scheduled)", -1, "nonnegative integer"),
        ("Days for shipping (real)", float("inf"), "nonnegative integer"),
        ("Order Id", 1.5, "nonnegative integer"),
        ("Order Id", 0, "positive"),
        ("Order Item Id", "private-invalid-value", "nonnegative integer"),
        ("order date (DateOrders)", "private-invalid-date", "Invalid order dates"),
        ("Shipping Mode", "private-unknown-mode", "Unexpected category"),
        ("Order Country", " ", "blank text"),
        ("Order Status", "private-unknown-status", "Unexpected category"),
    ],
)
def test_invalid_values_fail_without_echoing_values(frame, column, value, message):
    frame[column] = frame[column].astype(object)
    frame.loc[0, column] = value
    with pytest.raises(DatasetValidationError, match=message) as error:
        validate_dataset(frame)
    assert "private-" not in str(error.value)


def test_missing_schema_and_empty_data(frame):
    with pytest.raises(DatasetValidationError, match="missing required"):
        validate_dataset(frame.drop(columns=["Order Id"]))
    with pytest.raises(DatasetValidationError, match="no rows"):
        validate_dataset(frame.iloc[:0])


def test_repeated_item_id_is_rejected(frame):
    frame.loc[1, "Order Item Id"] = 1
    with pytest.raises(DatasetValidationError, match="Duplicate order item"):
        validate_dataset(frame)


def test_conflicting_order_outcomes_are_rejected(frame):
    frame.loc[1, "Late_delivery_risk"] = 0
    with pytest.raises(DatasetValidationError, match="Items in an order disagree"):
        validate_dataset(frame)


def test_conflicting_order_features_are_rejected(frame):
    frame.loc[1, "Order Country"] = "Another Synthetic Country"
    with pytest.raises(DatasetValidationError, match="Items in an order disagree"):
        order_features(frame)


def test_numeric_string_identifiers_are_normalized_before_grouping(frame):
    frame["Order Id"] = frame["Order Id"].astype(object)
    frame.loc[0, "Order Id"] = "10"
    assert validate_dataset(frame)["eligible_orders"] == 2
    assert len(order_features(frame)) == 2


def test_invalid_numeric_string_extension_dtype_is_rejected(frame):
    frame["Days for shipping (real)"] = frame["Days for shipping (real)"].astype(
        "string"
    )
    frame.loc[2, "Days for shipping (real)"] = "private-invalid-number"
    with pytest.raises(DatasetValidationError, match="nonnegative integer"):
        validate_dataset(frame)


def test_duplicate_dataframe_columns_are_rejected(frame):
    frame.columns = ["Order Id"] * len(frame.columns)
    with pytest.raises(DatasetValidationError, match="Duplicate column"):
        validate_dataset(frame)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("Late_delivery_risk", 1, "Delivery status and target"),
        ("Days for shipping (real)", 5, "duration rule"),
        ("Order Status", "CANCELED", "Cancellation indicators"),
    ],
)
def test_outcome_contradictions_are_rejected(frame, column, value, message):
    frame.loc[2, column] = value
    with pytest.raises(DatasetValidationError, match=message):
        validate_dataset(frame)


def test_all_canceled_is_rejected(frame):
    with pytest.raises(DatasetValidationError, match="No non-canceled"):
        validate_dataset(frame.iloc[3:])


def test_features_exclude_identifiers_outcomes_and_personal_fields(frame):
    for name in ("Customer Email", "Customer Password", "Latitude", "new_secret"):
        frame[name] = "private-sentinel"
    features = order_features(frame)
    assert list(features.columns) == list(FEATURE_COLUMNS)
    assert len(features) == 2
    assert features.index.tolist() == [0, 1]
    assert "private-sentinel" not in features.to_json()
    assert "private-sentinel" not in json.dumps(validate_dataset(frame))


def test_loader_selects_only_audit_columns_and_cli_is_reproducible(
    frame, tmp_path, capsys
):
    frame["Customer Email"] = "private-sentinel"
    path = tmp_path / "synthetic.csv"
    frame.to_csv(path, index=False)
    assert list(load_dataset(path).columns) == list(REQUIRED_COLUMNS)
    assert main(["--data", str(path)]) == 0
    first = capsys.readouterr()
    assert first.err == ""
    assert "private-sentinel" not in first.out
    assert len(json.loads(first.out)["dataset_sha256"]) == 64
    assert main(["--data", str(path)]) == 0
    assert capsys.readouterr().out == first.out


def test_cli_failures_do_not_echo_paths_or_records(tmp_path, capsys):
    path = tmp_path / "private-filename.csv"
    assert main(["--data", str(path)]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "private-" not in output.err
    path.write_text("Customer Email\nprivate-sentinel\n")
    assert main(["--data", str(path)]) == 1
    output = capsys.readouterr()
    assert "private-" not in output.err


def test_duplicate_headers_are_rejected(tmp_path):
    path = tmp_path / "synthetic.csv"
    path.write_text("Order Id,Order Id\n1,1\n")
    with pytest.raises(DatasetValidationError, match="Duplicate column"):
        load_dataset(path)
