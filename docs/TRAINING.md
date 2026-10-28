# Model training and evaluation: version 1

## Frozen experiment design

Milestone 4 uses the existing contract and preparation v1: one non-canceled order,
five approved shipping-plan/geography inputs, fixed chronological partitions,
and seven-day earlier-side gaps. IDs, dates, target, statuses, actual duration,
and customer fields are not prediction inputs. Each candidate is a scikit-learn
Pipeline with a fresh training-only ColumnTransformer followed by its classifier.
Validation/test only call transform/predict; there is no train+validation refit.

The seed is 42. The three fixed candidates are:

| Candidate | Fixed configuration |
| --- | --- |
| Majority dummy | `DummyClassifier(strategy="most_frequent")`; always predicts the training majority class. |
| Logistic Regression | C=1, liblinear solver, max_iter=1000; standardized scheduled days and one-hot categories. |
| Random Forest | 100 trees, max_depth=10, min_samples_leaf=20, one worker; same five inputs/preprocessing. |

The dataset fits comfortably in memory and supports sparse one-hot inputs, making
the bounded forest a suitable nonlinear comparison without a new dependency.
Training imbalance is modest (22,693 late / 16,875 not late, about 57.4% late).
No class weights, resampling, or target encoding are used. No training accuracy
is reported as evidence of future performance.

Before test prediction, choose the candidate/threshold maximizing validation F1
over the fixed grid 0.05, 0.10, ..., 0.95. For threshold ties prefer closest to
0.50, then the lower threshold. Model ties use higher validation PR-AUC, then
simplicity (dummy, logistic, forest). This criterion was declared before inspecting
model validation results. It is a portfolio baseline, not an established business
cost function. F1 can favor very broad positive predictions when late is common.

All candidates report validation metrics at both 0.50 and their selected threshold.
Accuracy, precision, recall, F1, ROC-AUC, and PR-AUC use late=1 as the positive
class. PR-AUC is **average precision**, not trapezoidal integration. Confusion
matrices have rows=true [not late, late], columns=predicted [not late, late]:
`[[TN, FP], [FN, TP]]`. Predictions use probability >= threshold.

## Probability calibration and selection tradeoff

Report Brier score and log loss (lower is better), plus ten fixed-width reliability
bins with count, mean predicted risk, and observed late rate. Expected calibration
error is the count-weighted absolute bin difference; it depends on binning and is
descriptive. These diagnostics do not prove probabilities are calibrated outside
this sample. The majority dummy assigns probability 1 to late and is consequently
poorly calibrated; a constant training-prevalence Brier reference is also recorded.

No calibrator is fitted on the validation set: that set is already used for model
and threshold selection. Proper future calibration needs a separate chronological
calibration interval or training-only temporal cross-validation. Test outcomes must
not fit a calibrator or revise this experiment's model/threshold.

Validation-only reproducibility selected Random Forest at 0.40. Its validation F1
is only slightly above always-late; Logistic Regression has better calibration
diagnostics. The selection rule remains unchanged. This is an important limitation,
not a reason to search for a more flattering result after seeing test performance.

## Single final test and immutable artifacts

`run_training()` writes a frozen `selection.json` and `pipeline.joblib`, then creates
an exclusive `test_evaluation.started` marker **before** the final test prediction.
Only the selected pipeline predicts test probabilities, once. Overall metrics,
calibration, and subgroups reuse that vector. There is no per-candidate test search.
Completed runs replay `evaluation.json` without fitting, predicting, or unpickling;
they verify the source fingerprint, model version, and artifact checksum first.
Partial runs fail closed rather than silently retrying the test.

This is a local operational guard, not a global experiment registry: creating a
different run directory could bypass it. Do not do so to repeatedly inspect this
test set. Future experiments need an explicit new evaluation plan and a fresh
holdout where possible. The original frozen result must remain intact.

Default ignored artifact directory: `data/processed/models/v1/`.

- `selection.json`: candidate parameters, validation metrics/calibration,
  explanation summaries, selected model/threshold, class counts and seed.
- `pipeline.joblib`: fitted preprocessing + selected classifier, threshold,
  model version, artifact schema version, feature names and sklearn version.
- `test_evaluation.started`: final-test guard marker.
- `evaluation.json`: frozen validation and test aggregates, subgroup results,
  feature importance, source/artifact checksums, versions and split policy.

No raw rows, identifiers, dates per order, customer fields, transformed training
matrix, or individual predictions are saved. Fitted encoders retain only approved
broad geography/shipping vocabularies; classifiers retain learned parameters/tree
statistics. These artifacts remain local and ignored, pending review for any
future public distribution. `joblib` is declared directly because serialization
uses it; it was already installed as a scikit-learn dependency.

Artifact schema version=1; training version=1; preparation/contract version=1;
model version=`v1`. Record exact installed versions and fixed parameters. This
supports same-environment reproduction, not guaranteed identical floating-point
results across platforms. Do not overwrite versions after changing semantics.

## Trusted loading and prediction schema

Pickle/joblib can execute arbitrary code. There is **no automatic model loading**
on module import or training replay. `load_model()` requires `trusted=True` and an
expected SHA-256, checks the same bytes before deserializing, then validates the
artifact schema, sklearn version, pipeline feature contract, and class order.
A checksum detects corruption; it does not establish that a publisher is trustworthy.
Never opt in for a user upload or arbitrary downloaded artifact.

Use only a locally produced, reviewed artifact and independently checked hash:

```python
from pathlib import Path
from freightguard.model_artifact import load_model

model = load_model(
    Path("data/processed/models/v1/pipeline.joblib"),
    expected_sha256="<verified local SHA-256 from evaluation.json>",
    trusted=True,
)
# model.predict(frame) accepts exactly the five approved fields.
```

Prediction requires finite nonnegative integer scheduled days, nonempty category
strings, and an allowed shipping mode. Missing/extra/duplicate fields are rejected
without echoing values. Unseen broad geography is encoded safely by the fitted
encoder. Output contains only `late_probability` and binary `late_prediction`.
Do not send customer records to this interface. No API/frontend is implemented.

## Subgroups and limitations

Report shipping-mode, market, and broad-region test metrics only when a group has
at least 100 orders and at least 10 in each class. Suppress smaller group labels
and record their count. AUC metrics are undefined for one-class samples. These
descriptive comparisons are not fairness guarantees or independent experiments.

The limitations in `PREPARATION.md` still apply: cancellation exclusions are based
on future outcomes, data is historical retail supply-chain data, later geography
is narrower, label availability/censoring is uncertain, repeated customers may span
partitions, and provenance/license are unverified. Feature availability at checkout
is an assumption. Feature importance/coefficients show associations, not causes;
redundant schedule/mode/geography fields can share importance. No business alert
costs or operational capacity limits justify the F1 threshold yet.

## Results

Frozen v1 results, 2026-10-28. Validation has 9,497 orders; final test has 13,071.
These are historical holdout measurements, not real-world deployment accuracy.

| Validation candidate | Threshold | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Always-late majority | 0.50 | 0.5660 | 0.5660 | 1.0000 | 0.7228 | 0.5000 | 0.5660 |
| Logistic Regression | 0.30 | 0.5674 | 0.5669 | 0.9981 | 0.7231 | 0.7398 | 0.8235 |
| Random Forest (selected) | 0.40 | 0.5790 | 0.5753 | 0.9790 | 0.7247 | 0.7426 | 0.8253 |

For context, the unselected **validation-only** operating point at 0.50 gives
Logistic Regression accuracy 0.6934, precision 0.8744, recall 0.5351, F1 0.6639;
Random Forest accuracy 0.6940, precision 0.8298, recall 0.5779, F1 0.6813.
The higher F1 at the selected thresholds comes from catching nearly all late
orders while issuing many more false alarms. A different business cost function
could favor another operating point, but it was not used to revise this experiment.

Validation confusion matrices (rows=true; columns=predicted; 0 then 1):

| Candidate | TN | FP | FN | TP |
| --- | ---: | ---: | ---: | ---: |
| Majority at 0.50 | 0 | 4,122 | 0 | 5,375 |
| Logistic at 0.30 | 24 | 4,098 | 10 | 5,365 |
| Forest at 0.40 | 237 | 3,885 | 113 | 5,262 |

**Final test, selected forest at 0.40:** accuracy 0.5756, precision 0.5756,
recall 1.0000, F1 0.7307, ROC-AUC 0.7494, PR-AUC 0.8345.
Confusion matrix: `[[0, 5547], [0, 7524]]`.

Every test order crosses 0.40, so the binary predictions behave exactly like
always-late. The increase in F1 from validation is not evidence of a better model;
test has a higher late prevalence (57.56% versus 56.60%). The scores have ranking
information, but this selected binary operating point is not useful for selective
alerts. We retain the frozen result rather than change the threshold after test.

### Calibration diagnostics

| Model/partition | Brier score | Expected calibration error |
| --- | ---: | ---: |
| Majority / validation | 0.4340 | 0.4340 |
| Logistic / validation | 0.1905 | 0.0092 |
| Forest / validation | 0.1914 | 0.0348 |
| Forest / test | 0.1888 | 0.0372 |

The constant training-prevalence validation Brier reference is 0.2457. Both
learned models improve on it; logistic calibration is better than the forest's
on validation. Full precision, log loss, and the reliability-bin counts/rates are
in ignored `evaluation.json`. A probability like 0.7 is an experimental model
score, not a guaranteed 70% real-world delay rate.

### Test groups with sufficient support

All reported groups have recall 1.0 and precision/accuracy equal to their late
rate because the selected threshold predicts all orders late. The score-level
AUC differences must be considered separately from these binary predictions.

| Shipping mode | Orders | Late rate | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Same Day | 731 | 0.5390 | 0.7004 | 0.5206 | 0.5525 |
| Second Class | 2,586 | 0.8055 | 0.8923 | 0.5032 | 0.8121 |
| Standard Class | 7,780 | 0.3950 | 0.5663 | 0.5094 | 0.4017 |

One shipping-mode group is suppressed under the per-class support rule. Within
these supported modes, ROC-AUC is near 0.5: much of the global ranking signal
comes from differences between modes, not distinguishing orders within a mode.

| Market | Orders | Late rate | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Europe | 7,691 | 0.5727 | 0.7283 | 0.7527 | 0.8299 |
| Pacific Asia | 5,380 | 0.5797 | 0.7340 | 0.7442 | 0.8299 |

| Region | Orders | Late rate | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Eastern Asia | 1,252 | 0.5807 | 0.7347 | 0.7458 | 0.8131 |
| Northern Europe | 1,644 | 0.5614 | 0.7191 | 0.7408 | 0.7983 |
| Oceania | 1,367 | 0.5794 | 0.7337 | 0.7415 | 0.7871 |
| South Asia | 1,088 | 0.5763 | 0.7312 | 0.7512 | 0.8138 |
| Southeast Asia | 1,673 | 0.5816 | 0.7354 | 0.7353 | 0.8197 |
| Southern Europe | 1,589 | 0.5626 | 0.7201 | 0.7571 | 0.8137 |
| Western Europe | 4,458 | 0.5805 | 0.7346 | 0.7488 | 0.8239 |

Full subgroup metrics, confusion matrices and calibration bins are saved in the
evaluation metadata; no individual predictions or order IDs are saved.

### What the model learned

Forest impurity importance sums to about 68.78% for shipping mode, 29.59% for
scheduled days, and 1.63% across the three geography inputs. These are rough
associations and can be biased by correlated/high-cardinality fields. They are
not causal explanations. Logistic coefficients also give shipping mode a strong
role; additional standardized scheduled days have coefficient about -0.852
(longer allowance associates with lower late risk, holding its other inputs fixed).
Mode and scheduled days are related, so individual coefficients need caution.

In simple English: the models mainly learn that some service plans leave less
time for shipping. They learn little reliable order-specific detail from these
five fields. The selected threshold is too broad to prioritize interventions.
Future work needs an explicit alert cost/capacity objective, suitable additional
pre-dispatch information, and a fresh evaluation plan—not more tuning on this test.

No API/frontend was built. Milestone 4 engineering was subsequently accepted and
committed as `8e5410a`; the model was not approved as effective binary alerts.

## Follow-up review: milestone 4.1

[Validation-only quality diagnostics](MODEL_QUALITY.md) investigate within-mode
ranking and capacity policies using the frozen model. These are exploratory
validation results, separate from the final test above. No threshold or original
test metric was changed; no second test prediction/evaluation was performed.
