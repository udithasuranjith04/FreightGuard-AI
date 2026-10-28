# Technical decisions

Status as of 2026-10-28. Separate existing choices from proposals so future
sessions do not mistake the roadmap for delivered functionality.

| Decision | Status | Reason |
| --- | --- | --- |
| Python 3.12, setuptools, `src/freightguard/` | Existing | Preserve the project's packaging and environment. |
| pandas, NumPy, scikit-learn | Existing | Already declared; sufficient for a small initial ML pipeline. |
| pytest and Ruff | Existing | Already declared developer tools. |
| Raw/processed data remain local and ignored | Required | Protect customer information and keep data out of Git. |
| Five-field feature allowlist | Implemented in milestone 2 | Only shared, broad order/shipping-plan fields; no personal or outcome fields. |
| Training-only ColumnTransformer | Implemented in milestone 3 | Scale scheduled days, one-hot encode four categories; no targets or metadata passed to fit. Classifier integration is future work. |
| FastAPI prediction backend | User requirement, pending implementation | Typed request validation and a clear API boundary. |
| Incremental milestones and learner-friendly explanations | Required | Make each change reviewable and understandable. |
| Simple single-service backend first | Proposed | Current scope does not justify distributed infrastructure. |
| Predict one order when its checkout shipping plan is finalized | Defined in contract v1 | Shipping mode, scheduled days, market, destination region/country are assumed known; availability is not proven by this snapshot. |
| Exclude canceled shipping outcomes, including suspected fraud | Defined in contract v1 | Cancellation is not successful on-time delivery; predictions are conditional on eventual non-cancellation. |
| Fixed chronological holdout with order isolation | Implemented in preparation v1 | Validation starts 2017-01-01; test starts 2017-07-01. No random shuffling or stratification. |
| Seven-day earlier-side maturity gaps | Implemented in preparation v1 | Exclude 761 orders near boundaries to reduce use of outcomes that might not yet be available. Label timing remains an assumption. |
| Unknown category handling and missing inputs | Implemented in milestone 3 | Unknown categorical values encode as zeros for their field; required missing inputs fail validation instead of being imputed. |
| Save aggregate metadata only | Implemented in milestone 3 | Dataset fingerprint/config/versions/counts recreate splits locally without publishing IDs, records, or fitted vocabulary. |

## Open decisions

- Confirm dataset provenance/license and real-world feature availability; snapshot
  data cannot prove when values were recorded. Contract v1 defines order-level
  predictions and cancellation handling; see `DATA_AND_ML.md` for limitations.
- Verify real label availability and revisit censoring for real operational data;
  the seven-day maturity assumption cannot be proven by this snapshot.
- Choose reproducible dependency version constraints/locking after checking the
  baseline environment; nothing is pinned beyond Python/build requirements yet.
- Choose frontend framework, chart library, API schema, and hosting provider in
  their respective milestones. Explain major architecture changes before acting.
- Decide how to distribute a public-safe model artifact and aggregate reports.
  Do not make the deployed application depend on the raw dataset.

Record future decisions with their date, evidence, tradeoff, and status. Avoid
adding databases, authentication, job queues, experiment platforms, or multiple
services without a demonstrated need and an agreed scope.
