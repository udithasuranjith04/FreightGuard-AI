# Project progress

## Current status

Milestones 1 and 2 are complete. The project has the original local inspection
script, a privacy-safe dataset contract/validation CLI, and synthetic tests.
No train/test preparation pipeline, trained model, API, or frontend exists yet.

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
