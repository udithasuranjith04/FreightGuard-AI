
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

Foundation and repository documentation complete. The existing Python inspection
script summarizes the local DataCo dataset. Training, FastAPI predictions, and a
responsive dashboard are planned; they are not implemented yet.

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
python -m ruff check .
python -m pytest
```

The inspection prints aggregate summaries. Current checks report one existing
import-layout lint issue and no collected tests. See
[development instructions](docs/DEVELOPMENT.md) for details and setup limitations.

## Project documentation

- [Agent instructions and coding standards](AGENTS.md)
- [Current architecture and Git audit](docs/ARCHITECTURE.md)
- [Dataset, privacy, and leakage prevention](docs/DATA_AND_ML.md)
- [Technical decisions](docs/DECISIONS.md)
- [Local development and deployment status](docs/DEVELOPMENT.md)
- [Implementation milestones](docs/MILESTONES.md)
- [Progress and outstanding work](docs/PROGRESS.md)

## Data and limitations

The local dataset is DataCo Smart Supply Chain. The candidate target is
`Late_delivery_risk`; feature selection, cancellation handling, and evaluation
are documented as pending decisions. Never commit raw customer records,
credentials, or secrets. Sensitive personal fields and delivery outcomes must
not become prediction inputs. Raw and processed data are ignored by Git.

Predictions are experimental until validated on representative
real-world logistics data.
