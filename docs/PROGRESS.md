# Project progress

## Current status

Milestones 1–4 and 4.1 are complete. Milestone 4 engineering is accepted and
committed; effective alerts are not approved. Validation-only quality investigation
is approved and committed as `1fec68c`. V1's threshold/test results remain frozen; no second test evaluation
or refitting occurred in 4.1. The local API is committed as `06461e7`; the Milestone 6 dashboard is committed as `d9cdf73`. Milestone 7 passed the independent final native/local audit; the user authorized
its source checkpoint. See FINAL_AUDIT.md and Git history for the handoff.
Docker runtime/image scans, remote CI and release approval remain pending. Recommendation: preserve the
educational baseline and redesign the data/problem before operational alerts.

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

## 2026-10-28 — Milestone 4 Git checkpoint

At the user's request, reviewed/staged fifteen completed milestone 4 paths alongside
the pre-existing script entry. Used explicit-path `git commit --only` to exclude
the script. Commit `8e5410a` succeeded with exactly the fifteen approved code/test/
documentation paths and no raw data/artifacts. Both versions of inspect_data.py
were preserved. This accepts engineering, not effectiveness as binary alerts.

## 2026-10-28 — Milestone 4.1: model quality and operational risk

### Focused plan

1. Snapshot frozen model/results/selection/test-guard hashes and preserve script work.
2. Load explicitly trusted v1; discard later rows before train/validation validation.
3. Examine validation score distributions, calibration, class errors, within-mode
   ranking, fixed threshold tradeoffs, and tie-aware capacity scenarios.
4. Compare training-only shipping-plan frequency references and grouped sensitivity.
5. Add reproducible diagnostics and synthetic tests; verify no fitting/test predictions
   or changes to the frozen threshold/results. Document an honest recommendation.

### Changes and validation-only findings

- Added `src/freightguard/diagnose_model.py`, `tests/test_diagnose_model.py`, and
  `docs/MODEL_QUALITY.md`; updated AGENTS, README, architecture, decisions,
  development, milestones, training follow-up, and this progress report.
- No existing model/training/evaluation code or dependency was changed. Separate
  ignored aggregate report: `data/processed/diagnostics/v1_validation.json`.
- All analysis uses 9,497 validation orders; frequency references use 39,568
  training orders. Original evaluation results are only preserved by identity;
  no new test probabilities or test performance are computed.
- At frozen 0.40, validation alert rate is 96.31%, FPR 94.25%, FNR 2.10%. Most
  not-late scores cluster above 0.40. Mean calibration errors vary by shipping mode.
- Within-mode ROC-AUC: Same Day 0.5003, Second Class 0.5078, Standard Class 0.5108.
  First Class has 1,429 validation orders, all late, so within-mode AUC is undefined.
- Top 10% (K=950): precision 100%, recall 17.67%, lift 1.7669 versus uniform review.
  The training-derived mode rule achieves the same. Top 20% (K=1900): forest
  precision 94.92%, recall 33.55%, lift 1.6771; mode rule precision 94.74%.
- Shipping mode explains 99.65% of frozen score variance on validation. Grouped
  shipping-plan permutation drops PR-AUC by 0.2596 on average; geography by 0.0013.
  These are descriptive sensitivity checks, not causality or new trained models.
- Boundary ties use uniform fractional expected credit and precision bounds,
  not favorable row ordering. Capacity scenarios and thresholds are exploratory;
  none is selected as a new model setting or evaluated on test.

### Checks and preservation

| Check | Final result |
| --- | --- |
| `python -m pytest -q` | 71 passed; synthetic data, no private dataset required. |
| Ruff on implemented modules/tests | Passed; new diagnostics files formatted. |
| Full-repository Ruff | Only preserved pre-existing I001 in inspect_data.py; exit 1. |
| Full-data reproducibility | Two diagnostic runs produce identical objects and byte-identical saved aggregate JSON. |
| No fitting/test predictions | Guarded real runs block Pipeline/forest fitting and assert all 22 scoring calls contain only 9,497 validation rows (base plus grouped permutations). |
| Frozen preservation | All four model-run file SHA-256 values match the pre-milestone snapshots; threshold remains 0.40. Script working SHA-256 and staged empty blob unchanged. |
| Privacy/Git | Raw data, original model files, and separate diagnostics output remain ignored; only .gitkeep files tracked under data/. Only the pre-existing script is staged. |
| Documentation/whitespace | Relative links resolve; Markdown and both Git whitespace checks pass. |

No second test evaluation was authorized or performed. No classifier or
preprocessing refit occurred in the real diagnostic runs.

### Recommendation and next checkpoint

Redesign the operational prediction problem/data before selective alerts. Keep v1
as an educational demonstration of honest model evaluation. A hypothetical 10%
review budget (20% scenario) illustrates capacity planning, but near-identical
service-plan reference performance does not justify promoting the forest as an
ML alerting improvement. Within-mode ranking is weak and validation has been reused.

Seek actionable timestamped pre-dispatch signals and a prospective holdout with
clear promised/actual outcomes and label availability. Predefine review capacity,
costs, and cancellation handling; request approval before implementing a redesign.
Do not tune on the original test or claim improved test performance.

Recommended checkpoint: `feat: add validation-only model quality diagnostics`.
Milestone 4.1 remains unstaged/uncommitted. Preserve inspect_data.py, all frozen
run files, and local data; no API/frontend work was performed.


## 2026-10-29 — Milestone 5: local educational FastAPI backend

### Plan and checkpoint

Verified HEAD `1fec68c` already contains exactly the eleven completed milestone
4.1 code/test/documentation paths, excluding inspect_data.py and all data/artifacts.
No duplicate commit was needed. Reviewed the existing uncommitted API draft and
completed it rather than replacing it. Plan: modular schemas/settings/app,
startup-only trusted loading, strict five-input validation, sanitized errors,
explicit CORS, synthetic tests, documentation, and preservation checks.

### Changes

Added/completed api/__init__.py, schemas.py, settings.py, app.py and test_api.py;
pyproject declares FastAPI, Pydantic, Uvicorn and dev HTTPX. API retains the
frozen v1 threshold 0.40 and existing loader. Unknown categories are rejected
using training vocabularies, also exposed as broad category lists in model info.
No fitting, test-set predictions, frontend, model changes, or artifact writes.
Updated AGENTS, README, architecture, development, milestones and this record;
added API.md with startup/trust/generation/error/examples/OpenAPI instructions.

### Verification

112 synthetic tests pass, including 41 API cases; one installed Starlette/HTTPX
TestClient deprecation warning remains. New API Ruff passes. Full Ruff exits 1
only for the preserved pre-existing I001 in inspect_data.py. Real trusted-artifact
synthetic request returned 200, risk 0.4272314668675644, experimental late at 0.40.
A first smoke request using English France correctly returned 422: frozen category
is Francia. Model info now exposes accepted spellings for discoverability.
No test cohort was scored. Frozen four-file hashes and both inspection-script
versions remain unchanged; data/artifacts remain ignored. Git diff whitespace
checks pass. Fresh online installation/public deployment not tested; current
Python 3.12 environment used successfully.

### Limitations and review checkpoint

V1 mainly models shipping plans, within-mode ranking is near chance, and all final
test predictions were late. Readiness means educational inference only. API has
no authentication or public deployment hardening; bind to loopback as documented.
No frontend built. Milestone 5 remains uncommitted for review. Suggested checkpoint:
`feat: serve frozen educational model through FastAPI` (exclude inspect_data.py).


## 2026-10-29 — Milestone 5 checkpoint and Milestone 6 dashboard

### Plan and preservation

Reviewed the API schemas/loading/error paths, existing M5 diffs and index. Re-ran
112 backend tests (passed) and API Ruff (passed) before committing exactly thirteen
M5 code/test/documentation paths as `06461e7`. Explicit-path commit excluded the
existing empty staged inspect_data.py; its working SHA-256 is still
`d5f6dce91efd15e32c122e12f33b7f859fbca40eacb05de71c1870e9f2087709`.

M6 plan: complete five responsive dashboard pages with React, strict TypeScript,
Vite/Tailwind and reusable UI; mirror the actual API contract, validate inputs and
network responses, surface honest status/errors/historical metrics; test critical
behavior, build/lint/type-check, regress backend, then verify synthetic predictions
through the two running local servers at desktop/mobile widths. Leave M6 uncommitted.

### Implemented

- Added frontend package/configuration/lockfile, public environment example, icon,
  responsive design system, hash navigation and accessible form/components.
- Overview, Shipment Prediction, Model Insights, API/System Status, About/docs.
  Exact five-input requests; category lists from actual model info. Runtime response
  validation, timeout, loading/empty/error/result states and reset/input-edit clearing.
- Actual health/info checks with refresh, separate model readiness and connectivity;
  historical figures sourced from TRAINING.md rather than fabricated live analytics.
- Historical importance bars, final test confusion counts and validation comparison.
  Honest all-late cutoff, non-cancellation, weak within-mode signal and no operational
  validation messaging. Only allowlisted public Markdown docs bundled/served.
- Synthetic unit/UI and real browser workflow tests; ignores for generated frontend
  files. Updated AGENTS, README, architecture/setup/milestone docs; added FRONTEND.md.
- No Python runtime changes, frontend/backend persistence, private datasets in the
  browser, serialized uploads, model edits, refitting or test-cohort evaluation.

### Validation

| Check | Result |
| --- | --- |
| TypeScript strict checking | Passed (`npm run typecheck`). |
| Frontend ESLint | Passed, zero warnings (`npm run lint`). |
| Vitest/Testing Library | 29 passed across three files, on patched Vitest 4.1.12. |
| Production build | Passed; JS ~353 KB (~109 KB gzip), CSS ~22 KB; five allowlisted public docs emitted. |
| Browser integration | Six Chromium desktop/mobile checks pass: real five-input synthetic prediction, navigation/keyboard/docs/overflow, injected network/model failures. |
| Backend regression | 112 passed; one existing Starlette/HTTPX TestClient deprecation warning. |
| Ruff | API clean. Full repository exits 1 only for preserved inspect_data.py I001. |
| npm dependency audit | Zero vulnerabilities after replacing the older test runner with patched compatible 4.1.12. |
| Preservation/Git | Original script working hash and empty index blob unchanged; all four frozen artifact hashes unchanged; only data .gitkeep files tracked; generated frontend/data/artifact paths ignored; Git whitespace checks pass. |

Both servers ran locally. Synthetic shipment (4 days, Standard Class, Europe,
Western Europe, Francia) returned score 0.4272314668675644, displayed 42.7%,
experimental Late at frozen 0.40. Browser tests assert exactly five request keys
and explicit operational validation false. No private row or test cohort scored.
The same six checks also pass against the built production bundle through
`npm run preview`. Desktop/mobile screenshots were inspected. Keyboard skip link and table/page
responsive behavior checked; this is not a full assistive-technology certification.

Initial npm/port/browser sandbox restrictions were resolved through approved
network/process execution. Initial browser selectors were corrected to use
accessible roles and the complete percentage text. These were test harness
issues; the final browser suite passes. Production documentation tests accept
both development text/plain and static text/markdown response types. The current npm clean install was verified
against package-lock.json. No fresh Python environment installation was attempted.

Known non-failing tooling messages: installed ESLint 9 reports upstream version
support deprecation during npm install; Vite removes two misplaced PURE comment
annotations in Zod dependencies; browser runner reports NO_COLOR/FORCE_COLOR
precedence. No dependency vulnerabilities were reported by the final npm audit.

### Review checkpoint

Milestone 6 remains uncommitted, with no M6 files staged. Suggested commit:
`feat: add responsive educational logistics dashboard`. Review frontend source,
lockfile, environment example, ignore rules and docs only; exclude inspect_data.py
and all generated files. Model remains an educational shipping-plan demonstration,
not operationally validated. No public deployment or additional modeling work.


## 2026-10-29 — Milestone 7: final integration, QA and release preparation

### Plan, checkpoint and preservation

Reviewed all M6 source/config/docs and both index/working changes. Clean npm ci,
strict TypeScript, ESLint, 29 frontend tests and production build passed; 112
backend tests/API lint passed. Committed exactly 35 M6 files as d9cdf73 using an
explicit-path commit. No user script/data/artifacts/generated output included.
The empty staged blob and implemented working script are preserved. Its existing
Ruff import issue remains because changing it would alter the preserved version.

M7 plan: audit actual API/UI contracts and privacy/error/load paths; correct proven
issues with regressions; verify synthetic native integration/mobile/accessibility;
audit dependencies and reachable Git/public files; prepare local container/CI
candidates and portfolio/release documentation without externally publishing.

### Completed changes

- Backend rejects truncated/invalid category vocabulary contracts, keeps explicit
  CORS response policy on unexpected sanitized errors, and adds nosniff/no-referrer/
  no-store headers. A real-loader checksum-failure test blocks deserialization.
- Frontend rejects inconsistent score/classification responses rather than
  relabeling the model, safely reports invalid API URL configuration, and matches
  backend geography normalization. Added not-late/boundary/configuration tests.
- Axe WCAG A/AA checks cover all five pages at desktop/mobile sizes. Found/fixed
  secondary-text contrast and fade-opacity issues; retained original UI/layout.
  Added 320px overflow and displayed 422/503/500 error checks. Historical charts
  remain the original documented aggregate values, with no fake live analytics.
- Added exact observed Python runtime/dev snapshots, Dockerfile/context allowlist,
  local-only base Compose plus opt-in read-only artifact mount, unprivileged Nginx
  candidate with security headers, and read-only synthetic GitHub Actions checks.
- Added redacted source/history/bundle review aid and its synthetic test. Rewrote
  portfolio README with architecture, setup, metrics, limitations and screenshot
  instructions. Added SECURITY.md, DEPLOYMENT.md and RELEASE_CHECKLIST.md; expanded
  the UI docs allowlist to eight public files. Updated project memory/handoff.
- No model/training/evaluation code, frozen artifact, threshold or private dataset
  changed. No refit, test-cohort scoring, final release commit/tag/push or external
  deployment. M7 changes remain unstaged/uncommitted for review.

### Check results and boundaries

Backend: 119 passed; frontend: 38 unit/UI tests passed; TypeScript, ESLint and
production build passed. Ten production-bundle Chromium browser checks pass:
real synthetic inference at desktop/mobile widths, navigation/keyboard/docs,
offline/model-unavailable states, WCAG A/AA analysis across five pages, 320px
layout and actionable 422/503/500 errors. The synthetic original-v1 result remains
0.4272314668675644 -> 42.7%, experimental Late at 0.40, operational validation false.

Maintained-code Ruff passes with an explicit exclusion for the preserved script;
full Ruff reports only its original I001. Pip check passes. Exact-version Python
install dry-run matches the current environment. npm ci with the lockfile is
verified. npm audit and separate pip-audit checks (25 runtime + 9 additional dev
pins) report no known vulnerabilities. Audit tool lived in a temporary venv,
leaving project dependencies unchanged. Python pins have no distribution hashes;
fresh Linux/platform install is unverified.

The redacted scanner checked 115 reachable history blobs and 88 public working/build
files and found no token/key/literal-credential/email/private-path matches. It does
not certify absence of arbitrary PII/encoded secrets. Manual log-path/source review
found no customer records or real credentials. Only data .gitkeep files are tracked;
all four original artifact hashes and the script working hash/index remain intact.
Generated bundles/screenshots/log traces remain ignored and use synthetic inputs.

Compose/override/CI YAML parse successfully. Docker is not installed, so Docker
compose config, builds, container startup/security-header behavior and image scans
were not run. No remote CI executed. Native production-preview/browser integration
is verified; it does not substitute for container verification. Base image/action
tags remain mutable; review/pin identities before using them as release gates.

Known non-failing warnings: existing Starlette/HTTPX TestClient deprecation,
ESLint 9 upstream support notice, Zod PURE-comment build annotation, npm lifecycle
script-policy notice, NO_COLOR/FORCE_COLOR precedence, pip-audit missing-hash advice.
No automatic force-upgrade or untrusted artifact loading was performed.

### Release assessment and checkpoint

Local educational portfolio application is integrated and verified. Public hosting
and operational model approval remain blocked: unverified Docker/CI/Linux setup,
license/provenance/distribution review, hosting TLS/auth/rate/resource/logging review,
and the fundamental all-late/weak within-mode model result. Automated accessibility
is not full manual screen-reader/cross-browser certification. Release source needs
user review; no final release commit is made.

Recommended checkpoint after review:
`chore: prepare educational portfolio release and integration QA`.
Exclude inspect_data.py and every ignored/generated/private file. Consult the
release checklist before a tag, push, artifact distribution or public deployment.


## 2026-10-29 — Independent final release audit and authorized M7 checkpoint

Reviewed repository inventory, recent history, index, M7 diffs/new files, data/ML
contract, actual HTTP/client schemas, browser pages/tests, privacy/logging/load
paths and release documentation. Reran complete pytest (119 passed), full Ruff
(only preserved script I001), maintained-code Ruff (passed), pip check (passed),
npm ci/typecheck/lint (passed), 38 frontend tests, production build (passed), npm
and Python advisory audits (no known vulnerabilities). Ten production-browser
checks passed at desktop/mobile widths, including five-page axe/keyboard/layout
checks, real synthetic prediction and displayed API/unavailable error states.

Live health/info/OpenAPI/docs/ReDoc responded 200. Synthetic prediction remained
0.4272314668675644 / experimental Late / threshold 0.40 / not operationally
validated. Sensitive synthetic extra field rejected with 422, no value echo.
Existing dev server on 5173 was preserved; audit production preview used 5174,
PLAYWRIGHT_BASE_URL and an explicit temporary CORS origin. No model/data changes,
real training, diagnostic run or held-out scoring. Four artifact hashes, script
working hash and empty staged blob match their original identities.

Final corrections: ignore root .env.* variants; explicitly disable inherited model
trust in the no-trust startup example; allow a configurable browser test base URL.
Added FINAL_AUDIT.md with actual results and scoped verdict. Final native/local
verdict is READY FOR EDUCATIONAL PORTFOLIO RELEASE. Docker/CI/Linux/image checks,
license/distribution and external hosting gates remain pending and unclaimed.
Full Ruff exception and all known tool/model limitations are documented.

User authorizes an explicit-path Milestone 7 commit after passing these checks.
The checkpoint excludes inspect_data.py and all ignored/private/generated files.
Its identity is recorded in Git history/final handoff. No tag, push or external
deployment is performed. The original user script remains the only outstanding
staged/working change after that commit.
