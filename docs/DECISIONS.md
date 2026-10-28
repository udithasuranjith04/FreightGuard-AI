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
| Fitted preprocessing pipeline | Required for training, not implemented | Prevent training/serving differences and fitting on test data. |
| FastAPI prediction backend | User requirement, pending implementation | Typed request validation and a clear API boundary. |
| Incremental milestones and learner-friendly explanations | Required | Make each change reviewable and understandable. |
| Simple single-service backend first | Proposed | Current scope does not justify distributed infrastructure. |
| Predict one order when its checkout shipping plan is finalized | Defined in contract v1 | Shipping mode, scheduled days, market, destination region/country are assumed known; availability is not proven by this snapshot. |
| Exclude canceled shipping outcomes, including suspected fraud | Defined in contract v1 | Cancellation is not successful on-time delivery; predictions are conditional on eventual non-cancellation. |
| Chronological holdout with order isolation | Proposed | Better approximates future shipments and avoids splitting an order's items. |

## Open decisions

- Confirm dataset provenance/license and real-world feature availability; snapshot
  data cannot prove when values were recorded. Contract v1 defines order-level
  predictions and cancellation handling; see `DATA_AND_ML.md` for limitations.
- Set chronological split boundaries in milestone 3 and retain whole orders.
- Choose reproducible dependency version constraints/locking after checking the
  baseline environment; nothing is pinned beyond Python/build requirements yet.
- Choose frontend framework, chart library, API schema, and hosting provider in
  their respective milestones. Explain major architecture changes before acting.
- Decide how to distribute a public-safe model artifact and aggregate reports.
  Do not make the deployed application depend on the raw dataset.

Record future decisions with their date, evidence, tradeoff, and status. Avoid
adding databases, authentication, job queues, experiment platforms, or multiple
services without a demonstrated need and an agreed scope.
