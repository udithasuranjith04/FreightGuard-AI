# Dataset, privacy, and ML evaluation

## Local dataset

The user supplied the DataCo Smart Supply Chain dataset in `data/raw/`:

- `DataCoSupplyChainDataset.csv`: 180,519 rows and 53 columns in the local file.
- `DescriptionDataCoSupplyChain.csv`: field descriptions, not customer records.

Both files are ignored by Git. Read the main file as Latin-1, as the existing
script does. Exact download URL, dataset version, checksum, and redistribution
license have not been verified; record provenance and confirm terms before any
public redistribution. This audit used local files only.

The fields include order items, products, commercial amounts, locations,
timestamps, shipping mode, customer information, and observed outcomes. Rows are
order-item observations: 180,519 unique item IDs belong to 65,752 unique orders.
There are 45,902 multi-item orders and 114,767 repeated order-ID rows. These are
not duplicate shipments to discard blindly. Preserve raw files unchanged.

Milestone 2 fingerprint (SHA-256):
`fa6d022ed437155e1a2f0378710602848703c8a7f203f7ff5d77805bf8480aa6`.
The validation CLI recomputes this fingerprint without publishing file contents.

The local dictionary defines `Late_delivery_risk` as 1 for late and 0 for not
late. The existing inspection script reports:

| Aggregate | Count |
| --- | ---: |
| Label 1 | 98,977 |
| Label 0 | 81,542 |
| Fully duplicate rows | 0 |
| Missing `Product Description` | 180,519 |
| Missing `Order Zipcode` | 155,679 |

The original full-file inspection also found 8 missing customer last names and
3 missing customer postal codes; these fields remain excluded. All 12 columns
used by the new validator have zero missing values. It rejects missing required
fields, invalid integers/dates, unknown shipping/status categories, and duplicate
item IDs. It deliberately does not load the excluded personal fields. Missing
excluded-column totals above come from the original inspection, not the new CLI.

Every row with `Delivery Status = Late delivery` has label 1; the other delivery
statuses have label 0. In particular, 7,754 canceled shipments are labeled 0.
Contract v1 excludes those rows before any future splitting or training.
Of them, 3,692 have `Order Status = CANCELED` and 4,062 have
`Order Status = SUSPECTED_FRAUD`. The cancellation rule is delivery status
`Shipping canceled` OR either of those order statuses. The validator requires
these indicators to agree in this dataset, and fails if that assumption changes.

## ML problem definition: contract version 1

Predict **whether one order will exceed its scheduled shipping duration**, at
the moment its checkout shipping plan is finalized, before dispatch. The target
is the dataset's binary `Late_delivery_risk`, conditional on that order eventually
being non-canceled. This is a classification problem, not an estimate of days
late, an arrival timestamp, cancellation probability, or a delivery guarantee.

All items in each local order agree on the target, outcomes, order timestamp,
and five selected inputs. The validator checks that before any deduplication.
Use one row per eligible order, so a five-item order does not count as five
independent predictions. No item-level product/price features are aggregated.
`order_features()` selects the five shared inputs; `eligible_orders()` also keeps
IDs/dates/labels as local metadata for the preparation module. Neither trains.

After cancellation exclusions:

| Aggregate | Count |
| --- | ---: |
| Excluded orders | 2,855 |
| Eligible item rows | 172,765 |
| Eligible unique orders | 62,897 |
| Late item rows / not-late item rows | 98,977 / 73,788 |
| Late orders / not-late orders | 36,048 / 26,849 |

The order-level late rate is about 57.3%. Item-level totals must not be described
as independent shipment counts. Dates parse using `%m/%d/%Y %H:%M`; order times
span 2015-01-01 through 2018-01-31. There is no timezone metadata, so do not
invent one. Chronological splits are implemented in milestone 3; calendar features
remain excluded. See [preparation policy](PREPARATION.md).

Exclusion is retrospective: checkout cannot know a future cancellation. Any
future dashboard must describe the risk as conditional on non-cancellation.
The historical cohort can introduce selection bias and does not establish
performance on all new orders. Snapshot statuses such as `PENDING` can coexist
with delivery outcomes; they are not reliable evidence of event-time availability.

## Privacy policy

Never publish raw rows or customer examples, even as screenshots, notebook
outputs, test fixtures, API examples, error messages, or logs. Use synthetic
examples for the portfolio and aggregate statistics for reports.

Exclude names, emails, passwords, street addresses, `Customer Id`, and
`Order Customer Id` from model features. Conservatively exclude all
customer-prefixed fields for the first baseline, as well as latitude/longitude,
postal codes, and fine-grained destination city/state fields. Broad destination
country, region, and market may be considered after review. A field's presence
in a public dataset does not make it appropriate to expose.

Identifiers such as `Order Id` and `Order Item Id` may be used locally for split
integrity checks, but not as model features or public examples. Product IDs,
free text, and image URLs should remain outside the first baseline unless a
specific benefit and safe inference-time meaning are established.

Prefer a small feature allowlist over removing a few known sensitive columns
from all available columns. The existing script's five-column warning is an
informational check, not comprehensive privacy enforcement. Do not save raw
personal columns in processed datasets or model artifacts. Review fitted
encoders and reports for retained values before publishing artifacts.

## Prediction time and leakage

Contract v1 allows exactly these five shared order fields:

| Input | Availability assumption at finalized checkout |
| --- | --- |
| `Days for shipment (scheduled)` | Planned shipping allowance has been assigned; zero is valid for same-day service. |
| `Shipping Mode` | Customer/service shipping choice is finalized. |
| `Market` | Broad destination market is known. |
| `Order Region` | Broad destination region is known. |
| `Order Country` | Destination country is known. |

These are operational assumptions, not event-history facts proven by the
dataset. If a real system assigns the shipping plan later, move prediction to
that point or revise the allowlist. Do not silently substitute actual duration.

Every source column has a defined treatment below. The API will eventually need
only the five inputs; validation uses seven additional columns locally.

| Field/group | Baseline treatment and reason |
| --- | --- |
| `Late_delivery_risk` | Target only; never a feature. |
| `Delivery Status` | Exclude; directly reveals the target in the local data. |
| `Days for shipping (real)` | Exclude; observed shipping outcome. |
| `shipping date (DateOrders)` | Exclude; dispatch happens after finalized checkout. |
| `Order Status` | Exclude initially; includes lifecycle outcomes and cancellations. |
| `Days for shipment (scheduled)`, `Shipping Mode`, `Market`, `Order Region`, `Order Country` | Allowed inputs, subject to the checkout assumptions above. |
| `order date (DateOrders)` | Audit/split metadata only; calendar features deferred. |
| `Order Id`, `Order Item Id` | Local grouping/uniqueness metadata only; never features. |
| `Customer City`, `Customer Country`, `Customer Email`, `Customer Fname`, `Customer Id`, `Customer Lname`, `Customer Password`, `Customer Segment`, `Customer State`, `Customer Street`, `Customer Zipcode`, `Order Customer Id` | Exclude all customer-specific fields and identifiers under the conservative privacy policy. |
| `Latitude`, `Longitude`, `Order City`, `Order State`, `Order Zipcode` | Exclude precise/fine-grained geography. |
| `Type`, `Benefit per order`, `Sales per customer`, `Sales`, `Order Profit Per Order`, `Order Item Profit Ratio` | Exclude transaction/profit/aggregate fields; timing and meaning insufficiently established. |
| `Category Id`, `Category Name`, `Department Id`, `Department Name`, `Order Item Cardprod Id`, `Order Item Discount`, `Order Item Discount Rate`, `Order Item Product Price`, `Order Item Quantity`, `Order Item Total`, `Product Card Id`, `Product Category Id`, `Product Description`, `Product Image`, `Product Name`, `Product Price`, `Product Status` | Exclude item/product-specific fields from the order-level baseline; do not invent aggregation or stock timing. |

The allowlist is implemented in `FEATURE_COLUMNS`; all other columns are
excluded by explicit selection. Among the 172,765 non-canceled item rows,
`actual days > scheduled days` matches the label exactly (zero mismatches).
Across the raw dataset there are 4,423 mismatches, all in canceled observations.
Thus actual duration and delivery status expose the answer, rather than being
useful early-warning inputs. The validator checks these relationships for drift.
Very high future scores still require a leakage review.

## Reproducible validation

Run `python -m freightguard.validate_data`, optionally with `--data PATH` for a
local CSV. Exit 0 means contract checks passed; exit 1 means validation failed.
Successful JSON contains only aggregate counts, known schema names, date bounds,
and the fingerprint. Errors do not echo values, rows, or local filenames.
The validation command writes nothing. The separate preparation command saves
only ignored aggregate metadata, described in `PREPARATION.md`.

Required columns are the five inputs plus order/item IDs, order timestamp,
target, delivery status, order status, and actual shipping days. New/extra
columns are ignored, never automatically made into features. Required values
cannot be null; geography text cannot be blank; scheduled/actual days and IDs
must be finite nonnegative integers (IDs positive); item IDs must be unique;
known status/shipping categories are checked. Whole-order consistency, binary
labels, cancellation agreement, and outcome relationships are checked. At least
one non-canceled order must remain. Both target counts are always reported;
future training must ensure each split supports its chosen metrics.

Synthetic tests cover invalid schemas/types/dates/labels, missing data, repeated
items, conflicting order fields/outcomes, canceled/fraud exclusions, safe feature
selection, deterministic output, and privacy-safe errors. They require no raw
dataset. This validates the selected contract, not all 53 source columns or
causal realism. It is not an assertion that source outcomes are trustworthy.

## Preparation and future evaluation

Milestone 3 implements validated one-order selection, chronological splits at
2017-01-01 and 2017-07-01 with seven-day earlier-side gaps, and training-only
scaling/one-hot encoding. It preserves the five-input allowlist and integer
0/1 target. Validation/test transformations do not fit anything. Milestone 4
evaluates fixed pipelines; see [training results](TRAINING.md). These rules
continue to govern training:

1. Run contract validation and select one row per non-canceled order. Keep
   identifiers/timestamps as local split metadata, separate from model inputs.
2. Preserve the implemented final test interval; do not resplit based on scores.
   Whole orders remain in one partition. Exact date boundaries, gaps, sizes,
   and label distributions are recorded in aggregate preparation metadata.
3. Use training/validation data for model selection and threshold choice. Fit
   imputers, encoders, scaling, feature selection, and any resampling only inside
   training partitions, ideally through a scikit-learn Pipeline/ColumnTransformer.
4. Compare a dummy baseline with a simple classifier. Report precision, recall,
   F1, confusion matrix, ROC-AUC and PR-AUC where valid, alongside class balance
   and sample counts. Accuracy alone is insufficient. Examine probability
   calibration before calling a score a reliable risk probability.
5. Assess errors by public-safe groups such as shipping mode and broad region.
   Repeated customers can inflate results even without customer IDs as inputs;
   consider a customer-group robustness check with IDs used only locally.
6. Evaluate the frozen pipeline on the held-out test set once decisions are
   complete. Save feature schema, versions, seed/split policy, metrics, and
   threshold alongside the artifact. Serve the same fitted preprocessing.

Tests should use invented rows to check prohibited columns, unknown categories,
invalid inputs, and disjoint order groups across splits. These preparation tests
now exist. Historical validation/test metrics are documented in `TRAINING.md`;
they do not establish real-world performance.
Historical retail supply-chain data may not represent real freight operations;
the portfolio must state that limitation and avoid promising delivery guarantees.
