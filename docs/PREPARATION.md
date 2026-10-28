# Leakage-safe data preparation: version 1

Implemented in milestone 3. This prepares features and evaluation partitions;
it does not train a classifier, measure predictive performance, or save a model.
The prediction contract and privacy rules remain in `DATA_AND_ML.md`.

## Order selection and feature boundary

`eligible_orders()` validates the item-level input before collapsing it to one
row per non-canceled order. Conflicting order fields fail validation rather than
being silently discarded. Orders are sorted by parsed order timestamp, then order
ID, making results independent of the CSV's row order. Dates remain naive because
the source does not identify a timezone.

Each `OrderSplit` keeps four aligned objects in memory:

- `X`: only scheduled shipping days, shipping mode, market, destination region,
  and destination country, in the approved feature order.
- `y`: the unchanged binary label, explicitly stored as integer 0/1.
- `order_ids`: local metadata used to verify disjointness, not model inputs.
- `dates`: parsed local order timestamps used only for partitioning and summaries.

Customer columns and extra fields are discarded by selective loading. Post-delivery
fields are used only to validate historical outcomes and exclude cancellations;
they are removed from the order table before preparing `X`. No customer identities
or per-order assignments are saved in the metadata JSON.

## Why a chronological split

Eligible orders cover every month from January 2015 through January 2018:
19,995 orders in 2015, 19,955 in 2016, 20,910 in 2017, and 2,037 in January 2018.
A random split would mix older and newer conditions and could give an optimistic
picture of forecasting future orders. Fixed calendar boundaries are easier to
explain and reproduce than searching for a split that gives attractive scores.
There is no shuffling, stratification, or random seed.

The fixed defaults use earlier-side seven-day maturity gaps:

| Partition | Order timestamp interval | Orders | Not late / late |
| --- | --- | ---: | ---: |
| Train | Before 2016-12-25 | 39,568 | 16,875 / 22,693 |
| First gap | 2016-12-25 inclusive to 2017-01-01 exclusive | 382 | Excluded |
| Validation | 2017-01-01 inclusive to 2017-06-24 exclusive | 9,497 | 4,122 / 5,375 |
| Second gap | 2017-06-24 inclusive to 2017-07-01 exclusive | 379 | Excluded |
| Test | From 2017-07-01 inclusive | 13,071 | 5,547 / 7,524 |

All 62,897 eligible orders are accounted for: 62,136 assigned plus 761 excluded
by gaps. The earliest observed order is 2015-01-01 and the latest is 2018-01-31.
All items in an order have one timestamp, so no order straddles a boundary.
The implementation additionally checks that concatenated split IDs are unique.
Dates exactly at an evaluation start belong to that evaluation partition; dates
exactly at the earlier gap start are excluded.

Why gaps: a model evaluated on January 1 should not learn labels from December 31
orders that have not finished yet. Observed real shipping durations reach six
days, and the audited order-to-shipping-date elapsed times also reach six days.
Seven days is a conservative fixed buffer. The command fails if the configured
gap does not exceed the observed duration; it does not silently enlarge the gap
based on held-out outcomes. A new dataset may require an explicitly revised policy.

This remains an assumption about outcome availability. The source's shipping date
does not establish a reliable delivery/label-observation timestamp; it also does
not exactly match the integer duration for 9,737 item rows. No event history or
snapshot collection time proves when labels became available. Final-period
right-censoring and label timing must be revisited for real operational data.

## Preprocessing

`prepare_dataset()` builds a scikit-learn `ColumnTransformer` and calls
`fit_transform(X_train)` once. It calls only `transform()` for validation and test.
Targets are never passed to preprocessing.

- `StandardScaler` learns the training mean and scale for scheduled days only.
- `OneHotEncoder(handle_unknown="ignore")` learns vocabularies for the four
  categorical inputs from training only. An unseen category becomes an all-zero
  block for its field; it does not cause vocabulary expansion or refitting.
- Required missing values remain validation errors. No imputation, target
  encoding, resampling, feature selection, or calendar features are added.
- Extra columns are dropped. Matrices returned in `PreparedData` are CSR sparse
  matrices, regardless of whether a tiny synthetic transformer returns dense data.

The current dataset produces 196 transformed columns. Held-out rows have no
categories absent from training, but synthetic tests exercise that case. Unknown
category row counts are reported without publishing category values. An unseen
value is safely representable; that does not imply a model will perform well on it.

The preparation command's fitted preprocessor and matrices stay in memory.
Milestone 4 reuses the same preprocessing definition inside each candidate's
classifier pipeline and persists the selected train-fitted pipeline. It does not
independently fit held-out transforms; see `TRAINING.md` for the frozen evaluation.
If using cross-validation later, fit a fresh pipeline inside each training fold.

## Saved metadata and reproducibility

Run `python -m freightguard.prepare_data`. The default output is
`data/processed/preparation_metadata.json`, which is ignored by Git. It contains:

- Dataset SHA-256, preparation/contract versions, exact boundaries/gap, sort rule,
  and package/interpreter versions.
- The five feature names, transformation choices, and the training-only fit rule.
- Split counts, binary class counts, aggregate date ranges, output width, and
  unknown-category counts; total gap exclusions.

It contains no order IDs, per-order timestamps, transformed rows, customer data,
category vocabularies, or fitted objects. The dataset fingerprint plus fixed
policy recreates membership from the same local CSV. Byte-identical source and
the same environment produce byte-identical JSON; tests also compare matrices.
This records installed versions, but does not replace a dependency lockfile.
Bump the preparation version when changing partition or transformation semantics.

Repeated identical runs leave existing metadata intact. Different existing content
is not overwritten: use `--output` to choose a new local file. Custom boundaries
use `--validation-start YYYY-MM-DD`, `--test-start YYYY-MM-DD`, and `--gap-days N`.
Do not choose them based on model scores. Invalid/empty splits, single-class
splits, and insufficient gaps produce safe errors before fitting transformations.

## Tradeoffs before model training

- The later period has a narrower geography mix. The full 2017H2–January 2018
  period contains two markets/seven regions versus five markets/23 regions in
  the earlier training period. Future performance may reflect distribution shift.
  Chronology preserves that change rather than balancing it away.
- Losing 761 orders to gaps is a deliberate tradeoff for more credible timing.
  The exact seven-day availability assumption is not proven by the snapshot.
- Orders are isolated; repeat customers may still span periods. Customer-specific
  features are excluded, but this is not a claim of generalization to new customers.
- Cancellation exclusion uses eventual outcomes, so predictions remain conditional
  on non-cancellation and can carry retrospective selection bias.
- Required fields are complete here. Real APIs need a clear validation contract;
  encoding unknown categories is different from accepting missing required inputs.
- Test data has been audited for integrity and descriptive counts only. Do not tune
  a model, threshold, features, or boundaries against test performance. Fit/tune on
  training/validation and reserve the final test for the frozen evaluation.
- The dataset is old retail supply-chain data with unverified provenance/license
  and event timing. There are no real-world delivery guarantees or performance
claims. No classifier was trained in milestone 3; milestone 4's historical metrics
and important all-late threshold limitation are documented in `TRAINING.md`.
