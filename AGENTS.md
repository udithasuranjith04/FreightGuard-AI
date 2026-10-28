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

Milestones 1 (documentation) and 2 (dataset validation/problem definition) are
complete. No training, split pipeline, API, or frontend exists yet.
`python -m freightguard.validate_data` checks the version 1 order-level contract
and prints only aggregate JSON. Read `docs/DATA_AND_ML.md` before ML changes.
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
- Use only aggregate or synthetic examples in public artifacts. Review notebooks
  and saved artifacts for embedded customer information before sharing.

## Project memory

- `docs/ARCHITECTURE.md`: observed code, folders, dependencies, and Git history.
- `docs/DATA_AND_ML.md`: dataset facts, privacy, leakage, and evaluation decisions.
- `docs/DECISIONS.md`: accepted constraints and decisions still pending.
- `docs/DEVELOPMENT.md`: local setup and current checks; deployment status.
- `docs/MILESTONES.md`: incremental implementation plan and acceptance criteria.
- `docs/PROGRESS.md`: completed work, validation evidence, and next actions.
