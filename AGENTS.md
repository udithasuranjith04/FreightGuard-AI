# FreightGuard AI: project instructions

Build a professional portfolio application for shipment delay prediction while
keeping the code understandable to a Python learner. Preserve existing work.

## Start every milestone here

1. Read this file, `README.md`, `docs/PROGRESS.md`, and the relevant documents.
2. Inspect Git status and diffs, including the index. Do not overwrite, unstage,
   or bundle the user's unrelated changes.
3. Write a focused implementation plan and describe the expected checks.
4. Implement only the agreed milestone. Ask before destructive actions or major
   architecture changes. Explain any proposed replacement of working code.
5. Run appropriate tests and checks. Report failures and missing coverage honestly.
6. Update `docs/PROGRESS.md` and any affected architecture or data documentation.
7. Explain what was built, which files changed, and how to test it in simple
   English. Recommend a Git commit checkpoint; do not commit automatically.

## Current handoff

Milestones 1–4 and 4.1 (validation-only quality investigation) are complete.
Milestone 4 engineering is accepted; the model is not approved as effective binary
alerts. Milestone 5 local FastAPI backend is committed as `06461e7`.
Milestone 6 React/TypeScript dashboard is committed as `d9cdf73`.
Milestone 7 passed final native/local release audit and its source checkpoint
was authorized by the user. Read `docs/FINAL_AUDIT.md` for evidence and limitations.
Read `docs/SECURITY.md`, `docs/DEPLOYMENT.md`, and `docs/RELEASE_CHECKLIST.md`.
The user authorized the final Milestone 7 commit after passing checks.
No release tag, push or external deployment is authorized. Docker/remote CI
remain unverified; native integration is tested. Preserve inspect_data.py exactly
(including its existing Ruff issue) and keep all four frozen artifact hashes.
Read `docs/API.md` before API changes and `docs/FRONTEND.md` before frontend work.
Keep frontend metrics labeled historical; never invent shipment records or KPIs.
Frontend checks: `cd frontend`, then `npm run typecheck`, `npm run lint`,
`npm test`, and `npm run build`. Browser tests need both local servers.
`python -m freightguard.validate_data` checks the version 1 order-level contract
and prints only aggregate JSON. Read `docs/DATA_AND_ML.md` before ML changes.
`python -m freightguard.prepare_data` creates chronological order splits and fits
preprocessing on training inputs only. It saves ignored aggregate metadata, not
order records or fitted objects. Read `docs/PREPARATION.md` before training work.
Milestones 2/3 were committed as `dabc8c9`/`b50039b` at the user's explicit request.
Milestone 4 was committed as `8e5410a`; milestone 4.1 was committed as `1fec68c` and approved as exploratory.
Frozen local v1 artifacts live under ignored
`data/processed/models/v1/`. Read `docs/TRAINING.md` before using them.
Random Forest at 0.40 was selected on validation; final test was evaluated once.
It predicts every test order late at that threshold. Report this limitation honestly.
Do not change model/threshold or retest to improve the frozen result.
Read `docs/MODEL_QUALITY.md`: top-10% validation precision matches a simple shipping
mode rule, and within-mode ranking is near chance. The recommendation is to redesign
the data/problem for operational alerts while preserving v1 as an educational demo.
Diagnostics require explicit local trust/hash, discard test-period outcomes, do
not fit anything, and save separate ignored validation aggregates. No alternate
threshold or top-K policy has test approval. A second test evaluation needs explicit
user approval; do not bypass this restriction through a new run directory.
`src/freightguard/inspect_data.py` is existing user work: at the initial audit its
empty file was staged and its implementation was unstaged (`AM`). Preserve both
states unless the user explicitly asks to change them. Check current status rather
than assuming that snapshot remains true.

## Engineering standards

- Python requirement: `>=3.12,<3.13`; use the project's configured environment.
- Follow the existing `src/freightguard/` layout and `pyproject.toml`; keep modules
  small, use clear names, and add type hints to new functions.
- Ruff line length is 88. Use pytest for meaningful behavior tests with synthetic
  fixtures; tests must not require the private raw dataset.
- Add dependencies only when the milestone needs them. Explain the choice and
  update installation instructions. Avoid premature services or abstractions.
- Document commands from the repository root. Report actual check results rather
  than claiming the project is tested because a command was run.
- As functionality is added, use logging for operational events and useful errors;
  never log personal data, credentials, or complete request/dataset rows.

## Privacy and ML rules

- Never commit raw customer data, credentials, secrets, or derived records that
  identify people. Do not print dataset samples into chat, docs, logs, or tests.
- `data/raw/` and `data/processed/` are local-only except `.gitkeep`. Git ignore
  rules do not protect files that are already tracked: inspect proposed commits.
- Treat names, email, passwords, street addresses, customer identifiers, precise
  location and postal information as excluded model inputs. See
  `docs/DATA_AND_ML.md` for the conservative feature policy.
- Define prediction time and an explicit feature allowlist before training.
  Exclude the label, delivery status, actual shipping duration, and future events.
- Contract version 1 predicts one order at finalized checkout shipping-plan time,
  conditional on non-cancellation. Use only `FEATURE_COLUMNS` in `validate_data.py`.
  Future canceled/fraud-marked shipping outcomes are cohort exclusions, not inputs.
- Split before fitting preprocessing. Keep repeated order items together across
  partitions; protect a final test set. Use the same fitted preprocessing at
  training and inference. Never tune on final test results.
- Preserve preparation v1's fixed 2017-01-01/2017-07-01 boundaries and seven-day
  earlier-side gaps unless explicitly revising and documenting the policy. Do not
  adjust dates to improve scores. Bump preparation version for semantic changes.
- Keep IDs/timestamps/targets separate from `X`. Learn scaler statistics and
  categorical vocabularies only from training; use transform-only on held-out data.
- Training seed=42, three fixed candidates, validation-F1 selection. Completed
  `train_model` runs replay saved JSON without refitting/predicting/unpickling.
  Never bypass the test marker or create new run paths to retune on this holdout.
- Never automatically load serialized uploads/downloads. `load_model` requires
  explicit local trust and a checked SHA-256; a hash alone does not establish trust.
  Artifacts contain only the five-input pipeline, never records or customer fields.
- Use only aggregate or synthetic examples in public artifacts. Review notebooks
  and saved artifacts for embedded customer information before sharing.

## Project memory

- `docs/ARCHITECTURE.md`: observed code, folders, dependencies, and Git history.
- `docs/DATA_AND_ML.md`: dataset facts, privacy, leakage, and evaluation decisions.
- `docs/PREPARATION.md`: implemented split policy, preprocessing, metadata, and risks.
- `docs/TRAINING.md`: frozen model selection, final metrics, loading, and limitations.
- `docs/MODEL_QUALITY.md`: validation-only diagnostics, capacity policies, recommendation.
- `docs/DECISIONS.md`: accepted constraints and decisions still pending.
- `docs/DEVELOPMENT.md`: local setup and current checks; deployment status.
- `docs/MILESTONES.md`: incremental implementation plan and acceptance criteria.
- `docs/PROGRESS.md`: completed work, validation evidence, and next actions.
