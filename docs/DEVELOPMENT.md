# Development and validation

Run commands from the repository root. The inspected local `.venv` uses Python
3.12.10. In PyCharm, use the configured project interpreter. Future Codex
sessions should follow any available Python environment instructions before
running commands.

## Local setup

For the existing environment:

```sh
source .venv/bin/activate
python --version
```

For a new clone with Python 3.12 installed:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

The new-clone installation instructions follow the existing package metadata;
a clean online installation has not been tested in this documentation milestone.
There is no lockfile, so installations may resolve different dependency versions.
Do not recreate or replace a working environment unnecessarily.

Obtain the DataCo dataset separately under its applicable terms and place the
main CSV at `data/raw/DataCoSupplyChainDataset.csv`. Keep its dictionary at
`data/raw/DescriptionDataCoSupplyChain.csv` for reference. Do not add them to Git.

## Run the existing functionality

```sh
python -m freightguard.inspect_data
```

This requires the editable package installation and the local main CSV. Direct
execution also works: `python src/freightguard/inspect_data.py`. The milestone 1
smoke check executed that file's main block with the configured interpreter.
It prints aggregate counts and schema information, reads personal columns into
memory, and writes no output files. Do not replace the summaries with raw samples.
There is no web application or prediction command yet.

## Checks

```sh
python -m ruff check .
python -m pytest
git diff --check
git diff --cached --check
git status --short
git check-ignore data/raw/DataCoSupplyChainDataset.csv data/processed/example.csv .env
```

At milestone 1, the inspection script succeeds, Ruff reports an existing `I001`
import-layout issue in `inspect_data.py`, and pytest exits 5 because no tests
exist. Neither lint nor automated behavior coverage is currently green. Do not
run auto-fixes against user work as part of documentation-only changes. The
next data-validation milestone should add meaningful synthetic-data tests and
resolve lint with an explained, focused code change.

For documentation-only work, verify relative links, required files, whitespace,
and preservation of source/configuration files. Re-running the full dataset
inspection is unnecessary unless dataset assumptions or inspection code change.

## Git checkpoint safety

Review both staged and unstaged changes before committing. During the initial
audit, `inspect_data.py` had an empty staged version and an unstaged implementation.
A blanket commit could include that staged placeholder. Do not automatically
stage everything or change the user's index.

For a documentation-only checkpoint, review these exact paths:

```sh
git diff -- README.md
git status --short
git diff --cached
```

Suggested message: `docs: document project baseline and development milestones`.
After reviewing the new files, an explicit-path commit can avoid including the
already-staged script:

```sh
git add AGENTS.md README.md docs/ARCHITECTURE.md docs/DATA_AND_ML.md docs/DECISIONS.md docs/DEVELOPMENT.md docs/MILESTONES.md docs/PROGRESS.md
git diff --cached -- AGENTS.md README.md docs/
git commit --only -m "docs: document project baseline and development milestones" -- AGENTS.md README.md docs/ARCHITECTURE.md docs/DATA_AND_ML.md docs/DECISIONS.md docs/DEVELOPMENT.md docs/MILESTONES.md docs/PROGRESS.md
```

These are recommended manual commands, not actions performed by Codex. Review
the staged script separately before creating its own checkpoint. Never use
`git add -f` for customer data.

## Deployment status

Nothing is deployed and there are no deployment commands yet. Do not treat
`main.py` as an API server. The deployment milestone will document a tested local
frontend/API start sequence, environment variables without real secrets, build
steps, artifact loading, health checks, and hosting/rollback steps for the chosen
platform. Only a reviewed model and public-safe aggregates should be needed by
the deployed application; raw customer data must remain offline.
