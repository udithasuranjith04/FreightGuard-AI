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
timestamps, shipping mode, customer information, and observed outcomes. Treat
rows as order-item observations until grouping is validated; do not assume one
row equals one shipment. Preserve raw files unchanged.

The local dictionary defines `Late_delivery_risk` as 1 for late and 0 for not
late. The existing inspection script reports:

| Aggregate | Count |
| --- | ---: |
| Label 1 | 98,977 |
| Label 0 | 81,542 |
| Fully duplicate rows | 0 |
| Missing `Product Description` | 180,519 |
| Missing `Order Zipcode` | 155,679 |

Some customer fields also contain missing values; they remain excluded rather
than being repaired for modeling. Zero identical rows does not establish that
orders or customers are unique.

Every row with `Delivery Status = Late delivery` has label 1; the other delivery
statuses have label 0. In particular, 7,754 canceled shipments are labeled 0.
This is an outcome-definition issue: decide whether to exclude cancellations
from the prediction cohort before splitting or training. Document that rule.

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

Proposed baseline: predict at order placement, before shipment or delivery.
This needs confirmation in the data-contract milestone. A feature is eligible
only if its value would already be available at that time.

| Field/group | Baseline treatment and reason |
| --- | --- |
| `Late_delivery_risk` | Target only; never a feature. |
| `Delivery Status` | Exclude; directly reveals the target in the local data. |
| `Days for shipping (real)` | Exclude; observed shipping outcome. |
| `shipping date (DateOrders)` | Exclude for order-time prediction; future event. |
| `Order Status` | Exclude initially; includes lifecycle outcomes and cancellations. |
| Profit, benefit, and customer sales aggregates | Exclude until their calculation window and availability are established. |
| `Days for shipment (scheduled)`, `Shipping Mode` | Candidates only if confirmed known at order placement. |
| Broad destination geography, product category, quantity, price/discount | Candidates subject to privacy and availability review. |
| `order date (DateOrders)` | Candidate calendar features and time splitting after parsing/validating dates. |

The allowlist is not implemented. Do not interpret this table as approval to
train on every remaining numeric field. Very high model scores must trigger a
leakage review before being presented as a success.

## Evaluation plan (not implemented)

1. Validate schema, label values, dates, and order grouping; settle cancellation
   handling and the prediction unit. Check whether all items within an order
   share a consistent target and relevant attributes.
2. Reserve a final test set before fitting anything. Prefer a chronological
   holdout to approximate future orders, keeping whole orders in one partition.
   Determine how to handle orders crossing the cutoff. Measure class balance
   and document dates, sizes, and the fixed seed where randomness is used.
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
invalid inputs, and disjoint order groups across splits. No model has been
trained, no split has been selected, and no predictive performance is claimed.
Historical retail supply-chain data may not represent real freight operations;
the portfolio must state that limitation and avoid promising delivery guarantees.
