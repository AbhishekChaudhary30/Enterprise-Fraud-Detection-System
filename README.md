# Enterprise Fraud Detection System

A production-oriented foundation for an enterprise fraud detection platform. This repository currently contains **Phase 2**: project architecture, configuration, logging, dataset management, exploratory analysis, and a configurable machine learning training pipeline.

## Phase 1 Scope

- Python 3.12-compatible `src` package layout
- YAML configuration with environment variable overrides
- Project-root-relative paths using `pathlib`
- Console and daily rotating Loguru logs
- Automatic Credit Card Fraud Detection dataset download and extraction
- Dataset validation report covering schema, target, missing values, duplicates, dtypes, and statistics
- EDA report with class distribution, missing values, correlations, distributions, and fraud-vs-normal comparisons
- Reusable preprocessing, feature engineering, optional SMOTE, stratified train/validation/test splitting
- Logistic Regression, Random Forest, XGBoost, LightGBM, and CatBoost model support
- Configurable GridSearchCV or RandomizedSearchCV comparison with metric-based selection
- Versioned model, pipeline, artifact, feature list, and metadata persistence
- Configurable evaluation metrics, threshold optimization, diagnostic plots, SHAP explanations, error analysis, model cards, and experiment history

Prediction APIs, FastAPI, dashboard, Docker, monitoring, explainability, and automated tests remain reserved for later phases.

## Folder Structure

```text
configs/                         YAML configuration
 data/raw/                       Downloaded raw dataset
 data/processed/                 Future processed data boundary
 data/external/                  External data boundary
models/                          Future model artifact boundary
artifacts/                       Runtime artifact boundary
logs/                            Daily rotating application logs
reports/                         Validation and EDA reports
reports/figures/                 Generated EDA figures
notebooks/                       Analysis notebooks boundary
scripts/                         Phase 1 command-line scripts
src/enterprise_fraud_detection/  Importable application package
	features/                      Preprocessing and feature engineering
	modeling/                      Model factory and training orchestration
tests/                            Future test boundary
docs/                             Project documentation
.github/                          Repository guidance
```

## Installation

Python 3.12 is the supported runtime.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` when local overrides are needed. The default public Kaggle API URL is configured in `configs/config.yaml`; restricted networks can use a downloaded archive or set `DATASET_URL` to an accessible compatible ZIP URL.

## Running Phase 1

Download and validate the dataset:

```powershell
python scripts/download_dataset.py
```

Validate an existing raw CSV:

```powershell
python scripts/validate_dataset.py
```

Generate the EDA report and figures:

```powershell
python scripts/run_eda.py
```

Train and compare all enabled Phase 2 models:

```powershell
python scripts/train.py
```

Evaluate the latest trained model and generate Phase 3 outputs:

```powershell
python scripts/evaluate.py
```

Evaluation settings live under `evaluation` in `configs/config.yaml`. Outputs are written to `reports/evaluation/`, `reports/figures/evaluation/`, `reports/shap/`, and `reports/experiments.jsonl`.

Training configuration lives under `training` in `configs/config.yaml`. Set `smote_enabled`, split sizes, search strategy, selection metric, feature lists, and model search spaces there. Each run creates a new `models/vN/` and `artifacts/vN/` directory and never overwrites an existing version.

Outputs are written to `reports/`, `reports/figures/`, and `logs/`. The dataset always belongs in `data/raw/`.

## Project Roadmap

1. **Phase 1:** Foundation, configuration, logging, dataset management, and EDA
2. **Phase 2:** Feature engineering, preprocessing, model training, tuning, comparison, and versioning
3. **Phase 3:** Evaluation, threshold optimization, explainability, error analysis, model cards, and experiment tracking
4. **Phase 4:** FastAPI service and dashboard workflow
5. **Phase 5:** Docker, monitoring, enterprise observability, and deployment hardening

## Engineering Principles

- Configuration owns paths and runtime settings.
- Modules receive settings explicitly rather than relying on global state.
- Raw data is immutable input; generated outputs are separated by directory.
- Phase boundaries remain stable as later capabilities are added.
