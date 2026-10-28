# Implementation plan

Created before implementation on 2026-10-28. Milestones 1–4 are complete.
The user approved/requested commits for milestones 1–3, and authorized fixed
model training/evaluation in milestone 4. Milestone 4 remains uncommitted for
review. API/frontend work is not authorized in this session.

At every milestone: read instructions/progress, inspect Git changes, write a
focused plan, implement that scope, run relevant checks, explain the result in
simple English with file names and test commands, update `PROGRESS.md`, and
recommend a commit checkpoint. Explain any replacement of working code; ask
before destructive actions or major architecture changes.

| Milestone | Scope | Acceptance criteria |
| --- | --- | --- |
| 1. Repository baseline and documentation | Inspect source, directories, README, dependencies, local dataset metadata, and Git history; add project memory. | Accurate architecture/data/privacy/decision docs, runnable current commands, recorded check results, source and index preserved. |
| 2. Data contract and safe validation | Define prediction time, row/group unit, cancellation policy, feature allowlist, schema checks, and clear local input errors. | Synthetic tests reject invalid labels, missing required fields, and unsafe inputs; aggregate report uses no personal values; lint/checks pass. |
| 3. Preparation and split integrity | Implement reusable safe preprocessing and reproducible train/validation/test partitioning. | Whole orders stay within partitions; temporal policy is tested; fitted transforms use training data only; dataset stays local. |
| 4. Baseline training and evaluation | Compare dummy and simple classifier pipelines; save reviewed pipeline and metrics. | Reproducible command, held-out evaluation, confusion matrix and useful metrics/charts, leakage review, artifact metadata and documented limitations. |
| 5. FastAPI predictions | Add validated request/response schemas, artifact loading, health check, prediction endpoint, and privacy-safe logging. | Tests cover valid/invalid synthetic requests, unavailable model, and training/inference feature agreement; documented local run command. |
| 6. Responsive dashboard | Choose a simple frontend; add shipment form, risk result, model limitations, and aggregate/evaluation charts. | Works on mobile/desktop, validates inputs, handles loading/API failures accessibly, and displays no customer records; frontend checks and API smoke check pass. |
| 7. Reproducibility and deployment | Review dependency reproducibility, integrate appropriate automated checks, document local full-stack setup and selected hosting. | Clean setup/build/start instructions verified, end-to-end synthetic prediction checked, health/error logging verified, no data/secrets shipped; deployment instructions and portfolio README complete. |

Tests, logging, charts, and documentation should be added alongside the relevant
behavior, rather than all being deferred to milestone 7. Keep each implementation
small; split a milestone into substeps if its diff becomes difficult to explain.

## Milestone 2 focused plan (completed)

1. Re-read project instructions, progress, and the user's current script changes.
2. Use local aggregate checks to establish order grouping and cancellation
   semantics; confirm the prediction-time contract before training work.
3. Define a minimal reviewed input schema and feature allowlist; add a small
   validation helper using existing dependencies rather than a new framework.
4. Add synthetic fixtures covering missing columns, invalid labels, and privacy
   exclusions; make input errors understandable to a beginner.
5. Run tests/lint/smoke checks and update the data contract and progress record.
   Preserve the original script, including its existing lint issue, as explicitly
   requested by the user; do not apply the earlier suggested import fix to it.

## Milestone 3 focused plan (completed)

1. Inspect date coverage and temporal distribution using aggregate evidence.
2. Extend the validated order selector to preserve split metadata apart from X.
3. Implement fixed chronological boundaries, whole-order isolation, and maturity gaps.
4. Fit scaling/one-hot encoding on training inputs only; transform held-out inputs.
5. Save aggregate metadata and add synthetic tests for leakage and reproducibility.
6. Run dataset checks, tests, Ruff, and preservation checks; document tradeoffs.

## Milestone 4 focused plan (completed)

1. Preserve the established splits/five-input contract and declare selection rules.
2. Implement seeded majority, logistic, and bounded forest pipelines; fit train only.
3. Compare validation metrics/calibration and reproducibility; freeze the selection.
4. Predict test once with the selected pipeline; reuse probabilities for groups.
5. Save versioned ignored artifacts, strict trusted loading, schema tests and logs.
6. Run checks and document the all-late final operating point without retuning.

## Next: milestone 5 (not started)

FastAPI work requires a new request. Reuse the frozen pipeline/schema/loading
rules and display research limitations honestly. The selected threshold predicts
all test orders late; it is not a demonstrated selective-alert improvement.
Any new modeling experiment needs a documented fresh evaluation plan rather than
further optimization against this already-observed test set.

Outstanding work includes milestones 5–7. Historical model metrics exist;
production readiness, frontend framework, and hosting remain unestablished.
