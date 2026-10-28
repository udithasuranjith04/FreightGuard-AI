"""Leakage and split tests with invented orders; no private CSV is required."""

import json

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix, issparse

from freightguard.prepare_data import (
    SplitConfig,
    chronological_splits,
    main,
    prepare_dataset,
    save_metadata,
)
from freightguard.validate_data import (
    FEATURE_COLUMNS,
    ORDER_DATE,
    ORDER_ID,
    TARGET,
    DatasetValidationError,
)


@pytest.fixture
def orders():
    dates = [
        "12/23/2016 12:00",
        "12/24/2016 23:59",  # training
        "12/25/2016 00:00",
        "12/31/2016 23:59",  # first maturity gap
        "1/1/2017 00:00",
        "6/23/2017 23:59",  # validation
        "6/24/2017 00:00",
        "6/30/2017 23:59",  # second maturity gap
        "7/1/2017 00:00",
        "1/31/2018 12:00",  # test
    ]
    rows = []
    for index, timestamp in enumerate(dates):
        risk = index % 2
        scheduled = 0 if index == 0 else 4
        country = "Synthetic Known"
        if index in (4, 5):
            country = "Synthetic Validation Only"
        if index in (8, 9):
            country = "Synthetic Test Only"
        rows.append(
            {
                ORDER_ID: index + 1,
                "Order Item Id": index + 1,
                ORDER_DATE: timestamp,
                TARGET: risk,
                "Days for shipment (scheduled)": scheduled,
                "Days for shipping (real)": scheduled + risk,
                "Shipping Mode": "Standard Class",
                "Market": "Synthetic Market",
                "Order Region": "Synthetic Region",
                "Order Country": country,
                "Order Status": "COMPLETE",
                "Delivery Status": "Late delivery" if risk else "Shipping on time",
                "Customer Email": "private-sentinel",
            }
        )
    # Multiple items must not increase one order's contribution to the dataset.
    rows.append({**rows[0], "Order Item Id": 100})
    rows.append(
        {
            **rows[0],
            ORDER_ID: 99,
            "Order Item Id": 99,
            "Delivery Status": "Shipping canceled",
            "Order Status": "CANCELED",
            "Days for shipping (real)": 6,
        }
    )
    return pd.DataFrame(rows)


def test_one_order_per_row_and_exact_boundary_assignment(orders):
    splits, excluded = chronological_splits(orders)
    assert excluded == 4
    assert splits["train"].order_ids.tolist() == [1, 2]
    assert splits["validation"].order_ids.tolist() == [5, 6]
    assert splits["test"].order_ids.tolist() == [9, 10]
    all_ids = pd.concat([part.order_ids for part in splits.values()])
    assert all_ids.is_unique
    assert 99 not in all_ids.to_list()
    assert splits["train"].dates.max() < splits["validation"].dates.min()
    assert splits["validation"].dates.max() < splits["test"].dates.min()
    for part in splits.values():
        assert list(part.X.columns) == list(FEATURE_COLUMNS)
        assert part.y.tolist() == [0, 1]
        assert part.y.dtype == np.dtype("int64")
        assert part.X.index.equals(part.y.index)


def test_scaling_and_vocabulary_learn_only_from_training_features(orders):
    prepared = prepare_dataset(orders)
    scaler = prepared.preprocessor.named_transformers_["scheduled_days"]
    assert scaler.mean_.tolist() == [2.0]
    encoder = prepared.preprocessor.named_transformers_["categorical"]
    assert encoder.categories_[-1].tolist() == ["Synthetic Known"]
    assert list(prepared.preprocessor.feature_names_in_) == list(FEATURE_COLUMNS)
    for name, matrix in prepared.matrices.items():
        assert issparse(matrix)
        assert matrix.shape == (2, 5)
        assert np.isfinite(matrix.data).all()
        assert "private-sentinel" not in json.dumps(prepared.metadata)
        assert prepared.metadata["splits"][name]["orders"] == 2
    assert (
        prepared.metadata["splits"]["test"]["unknown_category_rows"]["Order Country"]
        == 2
    )


def test_held_out_changes_cannot_change_training_transforms(orders):
    original = prepare_dataset(orders)
    changed = orders.copy(deep=True)
    mask = changed[ORDER_ID].isin([5, 6, 9, 10])
    changed.loc[mask, "Days for shipment (scheduled)"] = 2
    changed.loc[mask, TARGET] = 1 - changed.loc[mask, TARGET]
    changed.loc[mask, "Days for shipping (real)"] = 2 + changed.loc[mask, TARGET]
    changed.loc[mask, "Delivery Status"] = changed.loc[mask, TARGET].map(
        {0: "Shipping on time", 1: "Late delivery"}
    )
    changed.loc[mask, "Order Country"] = "Another Unseen Country"
    updated = prepare_dataset(changed)
    np.testing.assert_array_equal(
        original.matrices["train"].toarray(), updated.matrices["train"].toarray()
    )
    for name in ("mean_", "scale_"):
        np.testing.assert_array_equal(
            getattr(original.preprocessor.named_transformers_["scheduled_days"], name),
            getattr(updated.preprocessor.named_transformers_["scheduled_days"], name),
        )
    original_encoder = original.preprocessor.named_transformers_["categorical"]
    updated_encoder = updated.preprocessor.named_transformers_["categorical"]
    for left, right in zip(original_encoder.categories_, updated_encoder.categories_):
        np.testing.assert_array_equal(left, right)


def test_unseen_categories_transform_without_refitting(orders):
    prepared = prepare_dataset(orders)
    encoder = prepared.preprocessor.named_transformers_["categorical"]
    categories = [values.copy() for values in encoder.categories_]
    unseen = prepared.splits["test"].X.copy()
    unseen["Order Country"] = "Never Seen Geography"
    unseen["Customer Password"] = "private-sentinel"
    transformed = prepared.preprocessor.transform(unseen)
    assert transformed.shape[1] == prepared.matrices["train"].shape[1]
    # The country occupies the final one-hot column in this synthetic schema.
    np.testing.assert_array_equal(csr_matrix(transformed).toarray()[:, -1], [0, 0])
    for before, after in zip(categories, encoder.categories_):
        np.testing.assert_array_equal(before, after)


def test_target_values_do_not_influence_preprocessing(orders):
    first = prepare_dataset(orders)
    flipped = orders.copy(deep=True)
    mask = flipped["Order Status"].eq("COMPLETE")
    flipped.loc[mask, TARGET] = 1 - flipped.loc[mask, TARGET]
    flipped.loc[mask, "Days for shipping (real)"] = (
        flipped.loc[mask, "Days for shipment (scheduled)"] + flipped.loc[mask, TARGET]
    )
    flipped.loc[mask, "Delivery Status"] = flipped.loc[mask, TARGET].map(
        {0: "Shipping on time", 1: "Late delivery"}
    )
    second = prepare_dataset(flipped)
    for name in first.splits:
        np.testing.assert_array_equal(
            first.matrices[name].toarray(), second.matrices[name].toarray()
        )
        assert first.splits[name].y.tolist() != second.splits[name].y.tolist()


def test_shuffle_and_duplicate_items_do_not_change_preparation(orders):
    original = orders.copy(deep=True)
    first = prepare_dataset(orders)
    shuffled = prepare_dataset(orders.sample(frac=1, random_state=42))
    assert first.metadata == shuffled.metadata
    for name in first.splits:
        pd.testing.assert_frame_equal(first.splits[name].X, shuffled.splits[name].X)
        pd.testing.assert_series_equal(first.splits[name].y, shuffled.splits[name].y)
        np.testing.assert_array_equal(
            first.matrices[name].toarray(), shuffled.matrices[name].toarray()
        )
    pd.testing.assert_frame_equal(orders, original)


@pytest.mark.parametrize(
    "config",
    [
        SplitConfig("not-a-date"),
        SplitConfig("2018-01-01", "2017-01-01"),
        SplitConfig(gap_days=0),
        SplitConfig(gap_days=6),  # observed duration must be strictly shorter
        SplitConfig("2017-01-01", "2017-01-05"),
        SplitConfig("2014-01-01", "2014-07-01"),
    ],
)
def test_invalid_or_empty_split_configuration_is_rejected(orders, config):
    with pytest.raises(DatasetValidationError):
        prepare_dataset(orders, config)


def test_single_class_split_is_rejected(orders):
    orders.loc[orders[ORDER_ID].eq(2), TARGET] = 0
    orders.loc[orders[ORDER_ID].eq(2), "Delivery Status"] = "Shipping on time"
    orders.loc[orders[ORDER_ID].eq(2), "Days for shipping (real)"] = 4
    with pytest.raises(DatasetValidationError, match="both target classes"):
        prepare_dataset(orders)


def test_contradictory_order_items_fail_before_deduplication(orders):
    orders.loc[orders["Order Item Id"].eq(100), "Order Country"] = "Conflicting"
    with pytest.raises(DatasetValidationError, match="Items in an order disagree"):
        prepare_dataset(orders)


def test_cli_metadata_is_reproducible_and_contains_no_record_data(
    orders, tmp_path, capsys
):
    dataset = tmp_path / "synthetic.csv"
    output = tmp_path / "metadata.json"
    orders.to_csv(dataset, index=False)
    args = ["--data", str(dataset), "--output", str(output)]
    assert main(args) == 0
    first = capsys.readouterr()
    content = output.read_bytes()
    assert first.err == ""
    assert "private-sentinel" not in first.out
    assert "Synthetic Known" not in first.out
    assert "order_ids" not in first.out
    assert len(json.loads(first.out)["dataset_sha256"]) == 64
    assert main(args) == 0
    assert capsys.readouterr().out == first.out
    assert output.read_bytes() == content


def test_metadata_never_overwrites_different_existing_work(tmp_path):
    output = tmp_path / "existing.json"
    output.write_text("keep this existing content")
    with pytest.raises(DatasetValidationError, match="already differs"):
        save_metadata({"new": True}, output)
    assert output.read_text() == "keep this existing content"


def test_cli_errors_are_sanitized_and_do_not_create_output(tmp_path, capsys):
    output = tmp_path / "metadata.json"
    assert (
        main(["--data", str(tmp_path / "private-path.csv"), "--output", str(output)])
        == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "private-" not in captured.err
    assert not output.exists()
