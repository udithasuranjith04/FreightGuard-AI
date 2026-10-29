
# FreightGuard AI

An AI/ML engineering project exploring shipment delay risk prediction
for freight forwarding and logistics operations.

## Objective

Develop a reproducible machine learning pipeline that uses shipment
information available at prediction time to estimate the risk of late
arrival.

## Planned capabilities

- Shipment data validation and exploratory analysis
- Data preprocessing and feature engineering
- Baseline model and model comparison
- Model evaluation and error analysis
- Automated tests
- Interactive prediction dashboard

## Project status

Documentation, validation, preparation, and baseline model evaluation are complete.
The baseline
problem is order-level delay prediction when the checkout shipping plan is
finalized, conditional on the order not later being canceled. Random Forest was
selected on validation, but its frozen threshold predicts every test order late;
this limits its usefulness for selective alerts. The local FastAPI backend serves educational predictions; the dashboard is
not implemented yet. See the full [evaluation and limitations](docs/TRAINING.md).

The engineering implementation is accepted; effective binary alerts are not.
Validation-only investigation shows that strong top-10% precision matches a simple
shipping-mode rule and within-mode ranking is near chance. We recommend retaining
v1 as an educational demonstration and redesigning the data/problem before
operational use. See [model quality and review policies](docs/MODEL_QUALITY.md).

## Local development

Use Python 3.12. From the repository root, activate your existing environment
with `source .venv/bin/activate`. For a fresh setup:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Keep the separately obtained dataset at
`data/raw/DataCoSupplyChainDataset.csv`. Run the existing inspection and checks:

```sh
python -m freightguard.inspect_data
python -m freightguard.validate_data
python -m freightguard.prepare_data
python -m freightguard.train_model
python -m ruff check .
python -m pytest
```

The original inspection prints aggregate summaries. The new validator reads only
12 approved columns, checks the dataset contract, and prints aggregate JSON with
a dataset fingerprint. Preparation uses one row per order, chronological splits
with seven-day gaps, and preprocessing fitted only on training inputs. It saves
aggregate metadata to ignored `data/processed/preparation_metadata.json`.
Training saves a versioned pipeline and aggregate evaluation under ignored
`data/processed/models/v1/`; completed runs replay results without retesting.
Do not delete that run to repeat test evaluation. Tests use synthetic data.
Full-repository lint still
reports the preserved inspection script's existing import-layout issue. See
[development instructions](docs/DEVELOPMENT.md) for details and setup limitations.

## Project documentation

- [Agent instructions and coding standards](AGENTS.md)
- [Current architecture and Git audit](docs/ARCHITECTURE.md)
- [Dataset, privacy, and leakage prevention](docs/DATA_AND_ML.md)
- [Data preparation, temporal splits, and tradeoffs](docs/PREPARATION.md)
- [Model selection, evaluation, trusted loading, and limitations](docs/TRAINING.md)
- [Validation-only quality investigation and recommendations](docs/MODEL_QUALITY.md)
- [Technical decisions](docs/DECISIONS.md)
- [Local development and deployment status](docs/DEVELOPMENT.md)
- [Implementation milestones](docs/MILESTONES.md)
- [Progress and outstanding work](docs/PROGRESS.md)

## Data and limitations

The local dataset is DataCo Smart Supply Chain. The target is `Late_delivery_risk`
for non-canceled orders; the five allowed inputs and evaluation plan are documented
in the data contract. Never commit raw customer records,
credentials, or secrets. Sensitive personal fields and delivery outcomes must
not become prediction inputs. Raw and processed data are ignored by Git.

Predictions are experimental until validated on representative
real-world logistics data.

## Run the backend

See [API setup, commands, examples, and configuration](docs/API.md).
The API exposes `/health`, `/model/info`, and `/predict`; interactive docs are
available at `http://127.0.0.1:8000/docs` after startup. Explicit local artifact
trust and SHA-256 verification are required for predictions.
