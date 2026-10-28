# Milestone 4.1: validation-only model quality investigation

## Scope and review decision

Milestone 4's engineering was accepted, but the model was not approved as an
effective binary alerting system. It was committed as `8e5410a` without the
pre-existing script changes or any dataset/model artifact.

This investigation uses the **frozen v1 forest**, its unchanged 0.40 threshold,
training-derived frequency references, and the original **9,497 validation orders**.
No classifier, encoder, scaler, or calibrator is fitted. No new test predictions
are requested. The four original run files are checked by SHA-256 before/after
analysis. All original test metrics and the threshold remain untouched.

These are exploratory results on data already used for model/threshold selection.
The known test failure motivated this investigation. Neither validation reuse nor
the diagnostics create a fresh independent evaluation. No improved test performance
is claimed, and no capacity policy has been tested on the held-out set.

## Reproducible implementation

`diagnose_model.py` provides training/validation-only loading and aggregate
diagnostics. Rows at/after 2017-06-24 are discarded by date before eligibility
checks touch their outcomes. The CSV parser reads approved columns, but test
labels cannot reach model scoring, reference calculations, or diagnostic functions.
No test split object is constructed. The data fingerprint must match frozen v1.

The runner requires explicit local artifact trust and the independently verified
model hash. It writes only `data/processed/diagnostics/v1_validation.json`, which
is ignored, using the existing non-overwrite helper. There are no record-level
predictions, customer fields, IDs, or review queues in the output.

```sh
python -m freightguard.diagnose_model \
  --trust-local-model \
  --expected-model-sha256 e3d46fa78998d13584ed7d7ea88bd321c69e2773aa9b6f18eab20eee73d0ddef
```

Only use that trust opt-in for the locally produced and reviewed v1 artifact.
Do not use it for arbitrary downloads/uploads. This SHA-256 is the original v1
artifact identity; it is not proof that another publisher is trustworthy.

## Score distribution, calibration, and class-specific errors

The validation late rate is 56.60%. The model scores are concentrated around
shipping-plan groups rather than spread smoothly over individual risk:

| Score quantile | All orders | Not late | Late |
| --- | ---: | ---: | ---: |
| Minimum | 0.3900 | 0.3900 | 0.3900 |
| 25% | 0.4236 | 0.4234 | 0.4246 |
| Median | 0.4270 | 0.4246 | 0.7709 |
| 75% | 0.7784 | 0.4285 | 0.8970 |
| Maximum | 0.9292 | 0.8065 | 0.9292 |

The frozen 0.40 threshold sits below most not-late scores. It flags 96.31% of
validation orders, with 3,885 false alarms and 113 missed late orders. The
false-positive rate is 94.25% of actual not-late orders; the false-negative rate
is 2.10% of actual late orders. High recall therefore hides a very large workload.

Existing validation calibration remains Brier 0.1914 and ten-bin expected
calibration error 0.0348. Mode-specific calibration shows why one overall number
is insufficient:

| Mode | Orders | Mean predicted probability | Observed late rate | Brier |
| --- | ---: | ---: | ---: | ---: |
| First Class | 1,429 | 0.9133 | 1.0000 | 0.0076 |
| Same Day | 509 | 0.5417 | 0.4990 | 0.2517 |
| Second Class | 1,814 | 0.7779 | 0.7878 | 0.1676 |
| Standard Class | 5,745 | 0.4217 | 0.3939 | 0.2393 |

The forest understates the observed First Class rate and overstates Standard
Class/Same Day mean risk. These are historical cohort associations, not claims
about shipping services in general. No probability calibration correction is
fitted or substituted into the frozen model.

## Within-mode ranking

Large one-class groups are described, but AUC is left undefined. Groups under
100 orders are suppressed. This is a separate exploratory policy from milestone
4's test subgroup table, which also required ten examples of each class.

| Mode | ROC-AUC within mode | PR-AUC | Top-10% precision | Lift versus random within mode |
| --- | ---: | ---: | ---: | ---: |
| First Class | Undefined (all late) | Undefined | 1.0000 | 1.0000 |
| Same Day | 0.5003 | 0.5344 | 0.6298 | 1.2620 |
| Second Class | 0.5078 | 0.7890 | 0.7703 | 0.9779 |
| Standard Class | 0.5108 | 0.3993 | 0.3988 | 1.0123 |

Global ROC-AUC 0.7426 conceals near-chance within-mode ranking. Same Day's top-K
spike is exploratory (only 509 total orders and many examined policies), not
reliable proof of an actionable subgroup. There are no uncertainty intervals or
multiple-comparison corrections supporting promotion of that result.

## How much comes from the shipping plan?

Training-only mean late-rate references use shipping mode, scheduled days, or
their joint combination. They are descriptive frequency lookups, with the
training prior for unseen combinations, not retrained versions of the forest.
They never use validation outcomes to set scores.

- Each reference produces validation ROC-AUC 0.7385 and PR-AUC 0.7776, versus
  forest 0.7426/0.8253. PR-AUC is average precision and can be sensitive to ties.
- Reference validation Brier is 0.1899, slightly better than forest 0.1914.
- Grouping the forest's validation scores by shipping mode alone explains
  **99.65% of their variance**; scheduled days/joint plan explain the same amount.
  This is descriptive score variance, not a causal explanation or accuracy measure.
- Five seeded grouped permutations reduce validation PR-AUC by 0.2596 on average
  when mode/scheduled days are shuffled together, versus only 0.0013 when the
  three geography inputs are shuffled together. Standard deviations across the
  five shuffles are 0.0041 and 0.0007; these are not confidence intervals.

Joint permutations preserve the mode/day pair and the geography triplet, but may
still create unrealistic cross-block combinations. They are sensitivity probes,
not interventions, feature selection, retraining, or grounds to change the model.
The evidence consistently points to shipping-plan grouping as the main signal.

## Review-capacity policies: validation only

For a cohort of N orders and capacity f, K=ceil(N*f). Precision@K is the expected
late fraction in the reviewed set, recall@K is the expected fraction of all late
orders reviewed, and lift is precision@K divided by that cohort's late prevalence.
Uniform review is the reference, not the always-late classifier's F1.

Tied scores at the capacity boundary receive fractional expected credit, with
best/worst precision bounds. Neither input row order, IDs, nor labels choose which
tied orders enter the queue. These are aggregates, not executable queue assignments.

| Validation capacity | K | Forest precision@K | Recall@K | Lift | Mode-reference precision@K |
| --- | ---: | ---: | ---: | ---: | ---: |
| 10% | 950 | 1.0000 | 0.1767 | 1.7669 | 1.0000 |
| 20% | 1,900 | 0.9492 | 0.3355 | 1.6771 | 0.9474 |

At 10%, the cutoff is about 0.9133 and 315 orders tie at the boundary; 260 tie
slots are filled in expectation. All tied validation outcomes are late, so both
precision bounds equal 1. At 20%, nine orders tie for seven boundary slots;
precision bounds are about 94.895%–95.000%. The forest's improvement over the
mode rule at 20% is only about 0.18 percentage points (roughly 3.4 additional
late orders per 1,900 reviews in expectation). No independent confirmation exists.

### Exploratory fixed-threshold tradeoffs

| Candidate threshold | Alert rate | Precision | Recall | False alarms | Missed late |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen 0.40 | 96.31% | 0.5753 | 0.9790 | 3,885 | 113 |
| 0.50 | 39.41% | 0.8298 | 0.5779 | 637 | 2,269 |
| 0.60 | 34.48% | 0.8797 | 0.5360 | 394 | 2,494 |
| 0.80 | 16.47% | 0.9802 | 0.2852 | 31 | 3,842 |
| 0.90 | 13.88% | 1.0000 | 0.2452 | 0 | 4,057 |

These are validation thought experiments. **The model threshold remains 0.40.**
A fixed probability cutoff cannot guarantee a review capacity as the population
changes. No alternative threshold has been evaluated on test in milestone 4.1.

## Proposed business policy and recommendation

A demonstration could show a **10% human-review budget** (20% as a capacity
scenario), sorted by risk. Break boundary ties uniformly without outcomes, or use
an independently specified auditable random assignment. Recompute the capacity
cutoff within each future review cohort; do not reuse 0.9133 as an SLA guarantee.
Compare against the transparent training-derived shipping-mode priority rule.
Display precision/recall as historical validation estimates only. Reviewing a
late order is not evidence that the review can prevent a delay or save money.

**Recommendation: redesign the prediction problem/data before operational alerts.**
Preserve v1 as an educational demonstration of honest evaluation and model
limitations. Do not promote the forest's top-K results as an ML improvement over
a service-plan rule. The top-K scenario can illustrate capacity planning, but it
has not earned adoption as a validated operational policy.

A revised approach should define an actionable breach at a precise review time,
such as a promised-deadline violation predicted before dispatch. Seek recent
shipment/event data with recorded feature availability and label-observation
times, planned/actual completion, carrier/route-level operational context, and
pre-dispatch backlog or capacity signals. Historical carrier performance must be
computed as of prediction time from earlier completed shipments only. Continue
to exclude customer identities and precise personal location. Define cancellation
handling explicitly rather than silently treating future cancellation as success.

Predefine review capacity and false-alarm/missed-delay costs with the business.
Compare a transparent service-plan reference, then incremental features/models,
using fresh temporal validation and a newly reserved prospective holdout. Current
validation has been explored repeatedly; the old test is already consumed. A new
evaluation plan/data collection needs approval before implementation. No API,
frontend, redesigned model, or second held-out evaluation was built/run here.
