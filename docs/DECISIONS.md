# Technical decisions

Status updated through milestone 7 on 2026-10-29. Separate existing choices from proposals so future
sessions do not mistake the roadmap for delivered functionality.

| Decision | Status | Reason |
| --- | --- | --- |
| Python 3.12, setuptools, `src/freightguard/` | Existing | Preserve the project's packaging and environment. |
| pandas, NumPy, scikit-learn | Existing | Already declared; sufficient for a small initial ML pipeline. |
| pytest and Ruff | Existing | Already declared developer tools. |
| Raw/processed data remain local and ignored | Required | Protect customer information and keep data out of Git. |
| Five-field feature allowlist | Implemented in milestone 2 | Only shared, broad order/shipping-plan fields; no personal or outcome fields. |
| Training-only ColumnTransformer | Implemented in milestones 3/4 | Scale scheduled days, one-hot encode four categories; each classifier pipeline fits only training inputs. |
| FastAPI prediction backend | Implemented in milestone 5 | Typed request validation and a clear API boundary. |
| Incremental milestones and learner-friendly explanations | Required | Make each change reviewable and understandable. |
| Simple single-service backend first | Proposed | Current scope does not justify distributed infrastructure. |
| Predict one order when its checkout shipping plan is finalized | Defined in contract v1 | Shipping mode, scheduled days, market, destination region/country are assumed known; availability is not proven by this snapshot. |
| Exclude canceled shipping outcomes, including suspected fraud | Defined in contract v1 | Cancellation is not successful on-time delivery; predictions are conditional on eventual non-cancellation. |
| Fixed chronological holdout with order isolation | Implemented in preparation v1 | Validation starts 2017-01-01; test starts 2017-07-01. No random shuffling or stratification. |
| Seven-day earlier-side maturity gaps | Implemented in preparation v1 | Exclude 761 orders near boundaries to reduce use of outcomes that might not yet be available. Label timing remains an assumption. |
| Unknown category handling and missing inputs | Implemented in milestone 3 | Unknown categorical values encode as zeros for their field; required missing inputs fail validation instead of being imputed. |
| Save aggregate metadata only | Implemented in milestone 3 | Dataset fingerprint/config/versions/counts recreate splits locally without publishing IDs, records, or fitted vocabulary. |
| Fixed candidates and seed 42 | Implemented in training v1 | Majority dummy, logistic, bounded single-worker forest; no test-dependent search. |
| Validation F1 selection | Frozen before final test | Fixed 0.05–0.95 grid; documented deterministic ties. Forest at 0.40 wins narrowly. |
| Retain all-late test result | Required for evaluation integrity | No post-test threshold changes. Ranking is informative, but selected binary alerts offer no advantage over always-late on test. |
| Calibration diagnostics only | Implemented in milestone 4 | Brier/log loss/reliability bins; no calibrator fitted on reused validation data. |
| Versioned local joblib pipeline | Implemented in milestone 4 | Ignored artifacts; explicit local trust plus checksum/version/schema checks before use; no automatic deserialization. |
| One final test prediction and immutable replay | Implemented in milestone 4 | Frozen selection and exclusive marker precede test; completed runs replay saved aggregates. |
| Engineering accepted; binary alert effectiveness rejected | Milestone 4 review | Professional implementation does not establish useful selective alerts. Original metrics remain unchanged. |
| Validation-only investigation | Implemented in milestone 4.1 | No refitting or test predictions; train-only frequency references, tie-aware capacity statistics, within-mode diagnostics, grouped permutation sensitivity. |
| No promotion of top-K as ML improvement | Milestone 4.1 recommendation | Top-10% precision matches mode reference; top-20% gain is ~0.18 percentage points on reused validation only. |
| Redesign before operational alerts | Recommendation, not implemented | Seek actionable point-in-time signals and a fresh evaluation plan. Preserve v1 as educational evidence. |

## Open decisions

- Confirm dataset provenance/license and real-world feature availability; snapshot
  data cannot prove when values were recorded. Contract v1 defines order-level
  predictions and cancellation handling; see `DATA_AND_ML.md` for limitations.
- Verify real label availability and revisit censoring for real operational data;
  the seven-day maturity assumption cannot be proven by this snapshot.
- Choose reproducible dependency version constraints/locking after checking the
  baseline environment; M7 records exact observed Python pins and npm has a lockfile,
  but hash/platform-complete Python locking remains open.
- Establish an alert cost/capacity objective and a fresh evaluation plan before
  optimizing beyond this frozen result. Do not retune on the existing test set.
- React/TypeScript/Vite/Tailwind and the strict five-field API schema are implemented.
  Historical charts use simple accessible bars/tables rather than a new chart runtime.
  Hosting provider, TLS/auth/rate limits and artifact distribution remain open.
- Decide how to distribute a public-safe model artifact and aggregate reports.
  Do not make the deployed application depend on the raw dataset.

Record future decisions with their date, evidence, tradeoff, and status. Avoid
adding databases, authentication, job queues, experiment platforms, or multiple
services without a demonstrated need and an agreed scope.


## 2026-10-29 — Integration and release preparation decisions

Keep the existing model/schema and simple separate frontend/backend. Fail closed
on malformed model vocabularies and inconsistent network responses. Use exact
Python environment snapshots and the npm lockfile without changing fitted objects.
Add axe to existing browser checks; correct measured text-contrast issues.
Prepare optional local Docker/Compose and read-only CI candidates, explicitly
unverified without Docker/remote CI. Do not create hosting resources or distribute
artifacts automatically. Preserve the user's inspection script despite its existing
lint issue. Release source remains subject to user review and license decisions.
