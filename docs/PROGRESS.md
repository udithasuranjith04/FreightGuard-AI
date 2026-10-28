# Project progress

## Current status

Milestones 1–4 are complete. Validation, preparation, baseline training, frozen
evaluation, and trusted local prediction/loading exist. No API/frontend exists.
The selected forest at 0.40 predicts all test orders late; this limitation is
documented and no post-test retuning was performed. Milestone 4 is uncommitted.

## 2026-10-28 — Milestone 1: document the baseline

### Plan and scope

Inspect the entire project-owned source/configuration/documentation, directory
inventory, available Git history, dependencies, and local dataset metadata.
Document findings and an incremental implementation plan. Do not implement new
features, modify the raw data, or rewrite existing code. Generated environments,
Git internals, and caches were inventoried rather than treated as source.

### Changes

- Added root `AGENTS.md` with the repeatable milestone workflow, coding standards,
  preservation rules, and privacy/ML constraints for future sessions.
- Added `docs/ARCHITECTURE.md`, `DATA_AND_ML.md`, `DECISIONS.md`,
  `DEVELOPMENT.md`, `MILESTONES.md`, and this progress record.
- Updated `README.md` with current functionality, setup/check commands, and links.
- Preserved `main.py`, package source, dependencies, ignore rules, dataset files,
  and the existing staged/unstaged script work. No Git commit or staging action.

### Findings and validation

| Check | Result |
| --- | --- |
| Git status/history/file inventory | Two available commits; only pre-existing user change was `AM src/freightguard/inspect_data.py` (empty index entry, implemented working file). |
| Configured environment | Python 3.12.10 in project `.venv`; dependencies already installed. |
| Existing inspection script smoke check | Passed; 180,519 rows, 53 columns, binary label counts and aggregate summaries; no raw rows displayed. |
| Dataset and privacy review | Main CSV and dictionary are ignored; delivery status reveals target; canceled shipments are included in label 0; no feature policy enforced yet. |
| `python -m ruff check .` | Exit 1: existing `I001` import-layout issue in `inspect_data.py`; left unchanged. |
| `python -m pytest` | Exit 5: no tests collected; no automated coverage yet. |
| Documentation and preservation checks | Passed: eight Markdown files checked for trailing whitespace/final newlines; all eight relative links resolve; four source/configuration SHA-256 hashes unchanged; all three Python source files parse; staged script entry unchanged; both Git whitespace checks pass. |

These checks establish the current baseline; they do not establish model quality
or application readiness. See `DEVELOPMENT.md` for commands and known gaps.
Git tracking checks confirmed only `.gitkeep` files under `data/` are tracked;
both local CSVs and representative processed/secret paths remain ignored.

### Next work and checkpoint

Start milestone 2 only when requested: define the prediction contract and safe
validation, then add synthetic tests. Resolve cancellation semantics, order
grouping, and feature availability before implementing a training pipeline.

Recommended documentation checkpoint:
`docs: document project baseline and development milestones`.
Review the existing staged script separately; use the explicit-path checkpoint
instructions in `DEVELOPMENT.md` to avoid including it in a documentation commit.

## 2026-10-28 — Milestone 1 Git checkpoint

At the user's explicit request, staged the eight documentation paths and checked
the exact index listing. The pre-existing empty staged script was also visible;
used `git commit --only` with the eight documentation paths to exclude it.
Commit `13a711ff4267a3a403665adad4c3aeedfd3679ea` succeeded and its tree diff
contains exactly `AGENTS.md`, `README.md`, and the six milestone 1 docs.
The script remained `AM`: staged blob
`e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`, working-file SHA-256
`d5f6dce91efd15e32c122e12f33b7f859fbca40eacb05de71c1870e9f2087709`.

## 2026-10-28 — Milestone 2: validation and ML problem definition

### Focused plan

1. Inspect aggregate label/status/duration relationships, order grouping, date
   parsing, missing values, and item identifiers using only approved columns.
2. Define prediction time/unit, cancellation policy, and a minimal feature allowlist.
3. Add reproducible validation and safe feature selection, with synthetic tests.
4. Run tests, lint, real-dataset validation, and preservation checks; update docs.
   Do not train, fit preprocessing, split the dataset, or change the user's script.

### Implementation and findings

- Added `src/freightguard/validate_data.py`: selective loading of 12 audit columns,
  schema/value checks, order consistency, cancellation handling, a five-input
  selector, sanitized failures, and deterministic aggregate JSON with fingerprint.
- Added `tests/test_validate_data.py` with invented fixtures and temporary CSVs;
  no raw dataset dependency and no new package dependencies.
- Defined one-order delay classification at finalized checkout shipping-plan time,
  conditional on eventual non-cancellation. Input availability is an explicit
  operational assumption, not proven by this snapshot.
- Found 65,752 orders in 180,519 item rows; 45,902 orders have multiple items.
  All order-level outcomes and allowed inputs agree within each order; item IDs
  are unique. Repeated order IDs are legitimate item structure.
- Excluded 7,754 canceled-shipping rows (2,855 orders), including fraud-marked
  shipping cancellations. Remaining: 62,897 orders, 36,048 late and 26,849 not late.
- Delivery status exposes the label exactly. Actual duration exceeding scheduled
  duration matches the label for every non-canceled row. Both stay out of inputs.
- No missing values in the 12 required audit fields. Excluded descriptions/postal
  fields have substantial missingness; original inspection totals are documented.
- Updated AGENTS, README, architecture, data/ML, decisions, development, milestones,
  and progress documents. Source data and the original script remain untouched.

### Validation

| Check | Final result |
| --- | --- |
| `python -m pytest -q` | 27 passed; all data is synthetic. |
| Ruff on new module/tests | Passed; both new files formatted with Ruff. |
| Full-repository Ruff | Only the preserved pre-existing `I001` in `inspect_data.py`; exit 1. |
| Real dataset CLI | Passed twice; output byte-identical, expected cohort counts and SHA-256 verified. |
| Schema documentation | All 53 source column names have a documented treatment. |
| Documentation | Relative links resolve; final newlines/trailing whitespace checked. |
| Git whitespace/preservation | Both diff checks pass; only the original script remains staged, with the original empty blob and unchanged working SHA-256. |

The validator writes no dataset/artifact files; no model was trained. The
milestone 1 commit tree confirms the script is absent, as requested. All
milestone 2 code and documentation changes remain unstaged for review.

### Next checkpoint and outstanding work

Suggested commit: `feat: validate dataset and define order delay prediction contract`.
Do not include the preserved `inspect_data.py` staged/unstaged work. No milestone 2
commit is made without a further request.

Next is milestone 3: one-order preparation and chronological split integrity,
with identifiers/timestamps separate from model inputs. Dataset provenance/license,
real operational feature availability, and future cancellation selection bias
remain limitations. No model or performance claim has been produced.

## 2026-10-28 — Milestone 2 Git checkpoint

At the user's explicit request, reviewed and staged exactly the ten milestone 2
paths, alongside the pre-existing empty staged script. Used an explicit-path
`git commit --only` to exclude that script. Commit `dabc8c9` succeeded with eight
documentation paths, `src/freightguard/validate_data.py`, and
`tests/test_validate_data.py`. Verified the committed path list, then confirmed
the script's original staged blob and working SHA-256 were unchanged. No raw
data or generated metadata was included.

## 2026-10-28 — Milestone 3: leakage-safe data preparation

### Focused plan

1. Audit date coverage and temporal distribution using aggregate statistics only.
2. Retain one validated eligible order and keep IDs/dates/targets separate from X.
3. Implement fixed chronological splits, whole-order isolation, and maturity gaps.
4. Fit scaling/encoding only on training X; safely transform held-out categories.
5. Save reproducible aggregate metadata; test leakage, boundaries, and preservation.
6. Update docs and explain tradeoffs before any future model training.

### Changes and findings

- Added `src/freightguard/prepare_data.py`: split configuration, aligned in-memory
  split objects, train-only ColumnTransformer, CSR matrices, safe CLI, and
  non-overwriting aggregate metadata output.
- Extended `validate_data.py` with `eligible_orders()`; `order_features()` reuses
  it. The helper preserves validated metadata for partitioning and sorts orders
  deterministically, while removing post-delivery fields. Existing checks remain.
- Added `tests/test_prepare_data.py`: synthetic tests for one-order selection,
  exact date boundaries/gaps, isolation, label preservation, train-only statistics
  and vocabularies, unknown categories, target independence, permutation stability,
  invalid policies, deterministic metadata, and safe output/error behavior.
- Updated AGENTS, README, architecture, data/ML, decisions, development, milestones,
  and this progress file; added `docs/PREPARATION.md` with detailed tradeoffs.
- Orders span every month from January 2015 to January 2018. Later geography is
  narrower; a temporal holdout preserves that shift instead of mixing it away.
- Fixed boundaries: validation 2017-01-01, test 2017-07-01, seven-day earlier-side
  gaps. Train: 39,568 orders; validation: 9,497; test: 13,071; gap exclusions: 761.
  Every partition contains both classes and there is no order overlap.
- The five inputs produce 196 transformed columns. Only training inputs determine
  scaling/vocabularies. Required missing inputs fail validation; unknown categories
  encode safely without refitting. Metadata records only counts/schema/config/
  versions/fingerprint/date bounds, not IDs, vocabularies, or individual records.
- Generated ignored `data/processed/preparation_metadata.json`. No processed
  records, fitted objects, or model artifacts were saved; no new dependencies.

### Validation

| Check | Final result |
| --- | --- |
| `python -m pytest -q` | 44 passed using synthetic data; includes all previous validation tests. |
| Ruff on implemented modules/tests | Passed; changed Python files formatted with Ruff. |
| `python -m ruff check .` | Exit 1 only for the preserved pre-existing `I001` in `inspect_data.py`. |
| Full-dataset preparation | Passed: 39,568 / 9,497 / 13,071 orders, 761 gap exclusions, 196 output columns, no order overlap. |
| Reproducibility | Shuffled full input reproduces split IDs, X/y/dates, metadata, and CSR matrix arrays exactly. Two CLI runs and the saved JSON are byte-identical. |
| Dataset preservation/privacy | Original dataset SHA-256 unchanged; both raw CSVs and generated metadata ignored; only `.gitkeep` files tracked under data/. |
| Script/index preservation | Original working SHA-256 and empty staged blob unchanged; only the pre-existing script remains staged. |
| Documentation/whitespace | Relative links resolve; Markdown whitespace and both Git diff checks pass. |

No classifier was trained and no predictive metrics were computed. Milestone 3
source/tests/docs remain unstaged for review; generated metadata stays local.

### Remaining risks and checkpoint

Seven days exceeds the observed six-day shipping duration, but actual label
availability is not documented. The order-to-shipping timestamp difference also
does not exactly match the integer duration in every row; final-period censoring
is uncertain. Historical retail data, temporal geography shift, repeat customers,
retrospective cancellation exclusion, unverified provenance/license, and unpinned
dependencies limit generalization and reproducibility outside this environment.
These are documented in `PREPARATION.md`; no production accuracy is claimed.

Recommended checkpoint: `feat: add leakage-safe chronological data preparation`.
Milestone 3 remains unstaged/uncommitted. Exclude the pre-existing script and all
local dataset/metadata files. Milestone 4 model training requires a new request.

## 2026-10-28 — Milestone 3 Git checkpoint

At the user's explicit request, staged and verified twelve milestone 3 paths,
alongside the preserved pre-existing empty staged script. Used `git commit --only`
with the twelve paths. Commit `b50039b` succeeded; its path list contains only
approved code/tests/docs and excludes the script/data/artifacts. Verified the
script still has the original staged blob and working SHA-256.

## 2026-10-28 — Milestone 4: model training and evaluation

### Focused plan and selection rule

1. Reuse chronological splits, gaps, one-order unit, and five approved inputs.
2. Train fixed majority DummyClassifier, Logistic Regression, and bounded forest
   candidates, each with fresh training-only preprocessing; seed 42.
3. Maximize validation F1 over thresholds 0.05–0.95 step 0.05. Threshold ties:
   closest to 0.50, then lower; model ties: higher PR-AUC, then simpler model.
4. Examine imbalance/calibration; reproduce train/validation results before test.
5. Freeze selection and artifact, mark final evaluation, predict test exactly once,
   and reuse that probability vector for overall/calibration/subgroup metrics.
6. Add safe versioned persistence/loading/schema tests, run checks, document risks.
   Do not build API/frontend or commit this milestone before user review.

### Changes

- Added `train_model.py`, `evaluation.py`, `model_artifact.py`, and synthetic
  `tests/test_training.py`; no existing working code was replaced.
- Declared already-installed joblib directly for serialization in pyproject.toml.
- Added `docs/TRAINING.md`; updated AGENTS, README, architecture, data/ML,
  preparation, decisions, development, milestones, and this progress report.
- Saved ignored `data/processed/models/v1/` selection, pipeline, test guard, and
  aggregate evaluation metadata. Artifact schema/training/preparation/contract
  versions are 1; model version v1. No customer records or individual predictions.
- Added privacy-safe logging of fixed candidate/run events. Serialized loading is
  opt-in for trusted local files, with checksum/version/feature contract checks.

### Frozen findings

Validation only selected Random Forest at threshold 0.40. No calibrator, test-based
parameter changes, or train+validation refit. Class imbalance is modest (~57.4%
late in training); no weights/resampling. Full-data validation predictions and
reports reproduced exactly across two independent fits before final evaluation.

| Partition/candidate | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Validation majority, 0.50 | 0.5660 | 0.5660 | 1.0000 | 0.7228 | 0.5000 | 0.5660 |
| Validation logistic, 0.30 | 0.5674 | 0.5669 | 0.9981 | 0.7231 | 0.7398 | 0.8235 |
| Validation forest, 0.40 | 0.5790 | 0.5753 | 0.9790 | 0.7247 | 0.7426 | 0.8253 |
| Final test forest, 0.40 | 0.5756 | 0.5756 | 1.0000 | 0.7307 | 0.7494 | 0.8345 |

Final test confusion: `[[0, 5547], [0, 7524]]`. Every test order is predicted late;
the selected binary operating point offers no advantage over always-late on test.
Global ranking is informative, but supported within-mode ROC-AUC is near 0.5.
Shipping mode/scheduled days account for about 98.4% of forest impurity importance;
the model mainly learns shipping-plan associations, not granular order information.

Validation Brier: logistic 0.1905, forest 0.1914, constant-prior reference 0.2457.
Logistic has better validation calibration; forest test Brier 0.1888, bin ECE 0.0372.
Full confusion matrices, calibration diagnostics, and supported shipping-mode,
market, and region results appear in TRAINING.md and ignored evaluation metadata.
Small/per-class-insufficient subgroups are suppressed. No training accuracy claimed.

### Validation and remaining risks

| Check | Final result |
| --- | --- |
| `python -m pytest -q` | 59 passed; all automated data fixtures are synthetic. |
| Ruff on implemented modules/tests | Passed; new files formatted with Ruff. |
| Full-repository Ruff | Only the preserved pre-existing `I001` in inspect_data.py; exit 1. |
| Full-data reproducibility before test | Two independent train/validation fits give identical reports, selection, and validation probabilities. |
| Final real test | Exactly one selected-pipeline prediction pass, reused for all metrics/calibration/groups; no other candidate test predictions. |
| Replay guard | Existing real run returns identical JSON with Pipeline.fit, predict_proba, and joblib.load patched to fail; no retest or automatic load. |
| Local artifact smoke check | Explicitly trusted checksum-verified v1 pipeline loads and predicts synthetic five-field input; artifact is 183,269 bytes. |
| Privacy/preservation | Raw CSVs and all four model-run files are ignored; only data .gitkeep files tracked; source fingerprint and script checksum/index unchanged. |
| Docs and whitespace | Relative links resolve; Markdown and both Git diff whitespace checks pass. |

The test was evaluated once; subsequent commands must only replay its saved result.

F1 favors broad positives in this cohort; the gain over majority is tiny on
validation, and binary test predictions are all positive. No operational alert
cost/capacity objective exists. Probabilities remain experimental. Historical
retail data, narrowing geography, future cancellation exclusions, uncertain label
timing/censoring, repeated customers, unverified provenance/license, and unpinned
dependencies remain risks. Do not retune on this test; a future modeling effort
needs a fresh evaluation plan. Nothing is deployed.

Recommended checkpoint after review:
`feat: add reproducible model training and frozen evaluation`.
Milestone 4 remains unstaged/uncommitted; preserve the existing script and ignore
all data/models/metadata. No API/frontend was built.
