# Current architecture

Audited on 2026-10-28. This describes the working tree, including uncommitted
user code, rather than claiming every file is in the latest commit.

## Repository map

```text
FreightGuard-AI/
├── AGENTS.md                  instructions for future sessions
├── README.md                  project overview and documentation links
├── pyproject.toml             Python package, dependencies, pytest/Ruff settings
├── main.py                    original PyCharm greeting example
├── src/freightguard/
│   ├── __init__.py             empty package marker
│   ├── inspect_data.py         local aggregate dataset inspection
│   ├── validate_data.py        version 1 dataset contract and aggregate CLI
│   └── prepare_data.py         chronological splits and training-only transforms
├── data/
│   ├── raw/                   ignored DataCo CSVs, tracked .gitkeep
│   └── processed/             ignored aggregate metadata, tracked .gitkeep
├── tests/                     synthetic validation/preparation tests and .gitkeep
├── docs/                      project documentation added in milestone 1
├── app/                       empty local placeholder
└── notebooks/                 empty local placeholder
```

Local `.venv/`, `.idea/`, caches, bytecode, and generated
`src/freightguard_ai.egg-info/` also exist and are ignored. Empty directories
without tracked files, such as `app/` and `notebooks/`, will not survive a clone.
Generated environment contents are not application source.

## Existing behavior

`inspect_data.py` resolves the project root relative to its own file, reads
`data/raw/DataCoSupplyChainDataset.csv` using pandas with `encoding="latin-1"`
and `low_memory=False`, and prints:

- Row and column counts, label distribution, and delivery-status cross-tabulation.
- Missing-value counts, full-row duplicate count, and column types.
- The names of five sensitive columns when present, with a warning.

It reads all columns into memory, including personal fields. The warning does
not remove them or enforce a feature policy. It does not print customer rows,
train a model, create output files, validate a full schema, or handle missing
files/columns with custom errors. `main.py` only prints a sample greeting; it is
not an application entry point.

Milestone 2 adds `validate_data.py` without changing the original inspection
script. It loads only 12 approved audit columns, validates types and order-level
consistency, excludes canceled shipping outcomes, and emits deterministic
aggregate JSON plus a SHA-256 of the input CSV. Invalid data produces a safe
error and nonzero exit status. `order_features()` returns only the five allowed
inputs, one row per eligible order, with identifiers removed. It fits nothing
and writes no data/artifacts. Tests use invented records and temporary CSVs.

Milestone 3 extends the validated selector with `eligible_orders()` to retain
parsed order dates/IDs and targets as separate split metadata. It preserves the
original inspection script. `prepare_data.py` creates deterministic chronological
splits with maturity gaps, separates `X` from `y`/IDs/dates, fits a ColumnTransformer
on training features only, and transforms held-out features without fitting.
It returns aligned split objects, fitted preprocessing, and CSR matrices in memory.
Only public-safe aggregate metadata is saved to ignored `data/processed/`.
See [preparation details](PREPARATION.md) for intervals and limitations.

## Dependencies and tooling

The package is `freightguard-ai` version `0.1.0`, built with setuptools (`>=68`)
and a `src` layout. Python is restricted to 3.12. Runtime dependencies are NumPy,
pandas, and scikit-learn; the `dev` extra adds pytest and Ruff. No dependency
lockfile or version bounds for these runtime/dev packages exist yet.

The inspected PyCharm environment uses Python 3.12.10 in `.venv`, with pip.
Installed versions at audit: NumPy 2.5.4, pandas 3.1.0, scikit-learn 1.9.1,
pytest 9.1.1, and Ruff 0.17.3. These are observed local versions, not a lockfile
or a guarantee about a fresh installation.

Pytest searches `tests/`; Ruff's configured line length is 88.
FastAPI, an ASGI server, frontend packages, logging configuration, CI,
deployment configuration, models, and evaluation reports are absent.
Synthetic pytest coverage now exists for the dataset contract; the original
milestone 1 observation that no tests existed is superseded by milestone 2.
Milestone 3 adds split-integrity, training-only fit, unknown-category, and
reproducibility tests using the existing dependencies; nothing new was installed.

## Git audit

The initial audit had two commits on `main` (also locally referenced by
`origin/main`; no fetch was performed). The requested checkpoints add two local
commits:

| Commit | Change |
| --- | --- |
| `fe2755e` | Initial Python project foundation; included generated package metadata. |
| `35d1b66` | Removed generated package metadata from tracking and ignored `*.egg-info/`. |
| `13a711f` | Milestone 1: eight documentation files only; user script excluded. |
| `dabc8c9` | Milestone 2: validation, tests, and documentation; user script excluded. |

No raw dataset files appear in those commits' file lists. The existing ignore
rules cover raw/processed contents except `.gitkeep`, `.env`, environments,
IDE state, and common caches. They are not a general secret scanner.

Before this documentation milestone, the only working change was
`AM src/freightguard/inspect_data.py`: an empty staged file and a 57-line
unstaged implementation. No code, index entries, or history were changed during
the documentation milestone. Commit `13a711f` was later explicitly requested
and verified; it preserved that script's staged blob and working checksum.
The explicitly requested milestone 2 checkpoint `dabc8c9` also preserved them.

## Direction and remaining work

```text
Local DataCo CSV → validation → safe features and data splits
                → fitted preprocessing/model → evaluation + saved artifact
Prediction form → FastAPI validation → same preprocessing/model → risk result
Dashboard       → public-safe aggregates and evaluation charts
```

Validation, order selection, splits, and preprocessing are implemented. Training,
evaluation, a persisted model artifact, API, and dashboard remain future work.

Start with one Python package and one FastAPI service, then choose a small
frontend after reviewing its needs with the user. There is no approved frontend
framework or hosting provider yet. A database, queues, microservices, and cloud
infrastructure are not currently required.
