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

## Run dataset contract validation

```sh
python -m freightguard.validate_data
# Optional: validate a different local DataCo-format CSV.
python -m freightguard.validate_data --data /path/to/local/dataset.csv
```

This command loads only the 12 approved audit fields (no customer columns), checks
the order-level contract, and prints deterministic aggregate JSON and a SHA-256
fingerprint. It exits 1 with a sanitized error if required data is invalid; it
does not train, split, or write any processed files. The exact five allowed
features and cancellation policy are in `DATA_AND_ML.md`.

## Run leakage-safe preparation

```sh
python -m freightguard.prepare_data
```

This validates the same local CSV, creates one-order chronological splits, fits
preprocessing on training inputs only, and transforms validation/test inputs.
Only aggregate metadata is saved to ignored
`data/processed/preparation_metadata.json`; it also prints the same JSON.
No model, transformed rows, order IDs, or fitted object are saved. All matrices
and the fitted preprocessor are available in memory through `prepare_dataset()`.

Repeated identical runs succeed without changing the metadata file. If a previous
file has different content, choose a new output rather than overwriting it:

```sh
python -m freightguard.prepare_data --output data/processed/preparation_review.json
```

Custom fixed boundaries are available through `--validation-start`, `--test-start`
(both YYYY-MM-DD), and `--gap-days`. Defaults and limitations are documented in
[preparation details](PREPARATION.md). Do not move boundaries based on model
scores. The command fails safely if a split is empty/single-class or a gap is
insufficient. The original validation command still writes no files.

## Train or replay the frozen model experiment

```sh
python -m freightguard.train_model
```

On a fresh local checkout with the private CSV, this fits the three fixed
train-only pipelines, selects on validation, and evaluates the winner on test
once. In the current workspace v1 is already complete: this command only verifies
identity/checksum and replays ignored `data/processed/models/v1/evaluation.json`.
It does not unpickle, refit, or recompute test predictions. Never delete that run
or choose new paths merely to retest the same holdout.

The directory also contains the selected pipeline, frozen selection, and test
guard. Partial runs stop for manual inspection. `--data`, `--run-dir`, and
`--model-version` support explicitly planned experiments; they are not a way to
tune against the frozen test. Full artifact trust instructions, metric meanings,
and subgroup results are in [training documentation](TRAINING.md).

Loading requires an explicitly trusted local artifact and verified SHA-256.
Never deserialize an uploaded/downloaded model automatically. Prediction accepts
exactly the five approved fields and rejects sensitive/extra columns.

## Checks

```sh
python -m ruff check .
python -m pytest
git diff --check
git diff --cached --check
git status --short
git check-ignore data/raw/DataCoSupplyChainDataset.csv data/processed/example.csv .env
```

At milestone 4, synthetic validation/preparation/training tests pass without raw data.
Ruff passes on the implemented modules/tests; full-repository Ruff still reports the
existing `I001` import-layout issue in `inspect_data.py`. That script is preserved
at the user's explicit request. Do not change it merely to make lint green.

To check only the new code:

```sh
python -m ruff check src/freightguard/validate_data.py src/freightguard/prepare_data.py src/freightguard/evaluation.py src/freightguard/model_artifact.py src/freightguard/train_model.py tests/
python -m pytest -q
```

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

The milestone 1 checkpoint was explicitly requested afterward and completed as
`13a711f`, with exactly the eight documentation paths above and no script. The
script's staged empty blob and unstaged implementation were verified unchanged.
Milestone 2 was subsequently committed as `dabc8c9`, containing only the ten
approved implementation/test/documentation files; script preservation was verified.
Milestone 3 was subsequently committed as `b50039b`, containing twelve approved
code/test/documentation paths; both script versions remain unchanged.
Milestone 4 remains uncommitted pending the user's review of the reported results.
Suggested checkpoint: `feat: add reproducible model training and frozen evaluation`.
Stage only its three new modules, training tests, `pyproject.toml`, and affected
documentation (including `docs/TRAINING.md`); use an explicit-path commit to
exclude the preserved script. Never stage generated models/metadata or raw data.

## Deployment status

Nothing is deployed and there are no deployment commands yet. Do not treat
`main.py` as an API server. The deployment milestone will document a tested local
frontend/API start sequence, environment variables without real secrets, build
steps, artifact loading, health checks, and hosting/rollback steps for the chosen
platform. Only a reviewed model and public-safe aggregates should be needed by
the deployed application; raw customer data must remain offline.
