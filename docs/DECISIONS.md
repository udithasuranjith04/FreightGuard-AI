# Technical decisions

Status as of 2026-10-28. Separate existing choices from proposals so future
sessions do not mistake the roadmap for delivered functionality.

| Decision | Status | Reason |
| --- | --- | --- |
| Python 3.12, setuptools, `src/freightguard/` | Existing | Preserve the project's packaging and environment. |
| pandas, NumPy, scikit-learn | Existing | Already declared; sufficient for a small initial ML pipeline. |
| pytest and Ruff | Existing | Already declared developer tools. |
| Raw/processed data remain local and ignored | Required | Protect customer information and keep data out of Git. |
| Explicit safe feature allowlist and fitted preprocessing pipeline | Required for training | Prevent sensitive inputs, leakage, and training/serving differences. |
| FastAPI prediction backend | User requirement, pending implementation | Typed request validation and a clear API boundary. |
| Incremental milestones and learner-friendly explanations | Required | Make each change reviewable and understandable. |
| Simple single-service backend first | Proposed | Current scope does not justify distributed infrastructure. |
| Predict at order placement | Proposed | Defines which facts can be known before predicting a delay. |
| Chronological holdout with order isolation | Proposed | Better approximates future shipments and avoids splitting an order's items. |

## Open decisions

- Resolve canceled orders and whether predictions represent order items, orders,
  or shipments before establishing the modeling contract.
- Confirm dataset provenance and license, prediction time, feature availability,
  and split boundaries. Validate the assumptions using aggregate evidence.
- Choose reproducible dependency version constraints/locking after checking the
  baseline environment; nothing is pinned beyond Python/build requirements yet.
- Choose frontend framework, chart library, API schema, and hosting provider in
  their respective milestones. Explain major architecture changes before acting.
- Decide how to distribute a public-safe model artifact and aggregate reports.
  Do not make the deployed application depend on the raw dataset.

Record future decisions with their date, evidence, tradeoff, and status. Avoid
adding databases, authentication, job queues, experiment platforms, or multiple
services without a demonstrated need and an agreed scope.
