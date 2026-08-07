# Enterprise Fraud Detection System

A production-ready enterprise fraud detection application. This repository contains the completed five-phase system: reproducible ML training, evaluation and explainability, authenticated serving, dashboard workflows, container packaging, automated quality checks, monitoring, drift detection, benchmarking, and documentation.

## Capabilities

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
- Versioned FastAPI endpoints for health, authentication, predictions, CSV workflows, models, reports, and history
- JWT authentication with admin role protection and process-cached model loading
- Streamlit dashboard for predictions, uploads, metrics, plots, SHAP outputs, history, and administration

Phase 5 is the final release hardening layer. Cloud deployment and deployment-specific CI/CD remain intentionally outside this repository.

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
scripts/                         Training, evaluation, serving, drift, and benchmark commands
dashboard/                       Streamlit dashboard
src/enterprise_fraud_detection/  Importable application package
	features/                      Preprocessing and feature engineering
	modeling/                      Model factory and training orchestration
	serving/                       Model loading and prediction services
	auth/                          JWT authentication
	api/                           FastAPI application and routers
	evaluation/                    Metrics and explainability
tests/                            Unit and API behavior tests
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

## Running the System

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

Start the FastAPI backend:

```powershell
python scripts/start_api.py
```

The versioned API is available at `http://127.0.0.1:8000/api/v1`; Swagger UI is at `http://127.0.0.1:8000/docs`.

Start the dashboard in another terminal:

```powershell
python scripts/start_dashboard.py
```

Set `JWT_SECRET`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` in `.env` before shared or non-local use.

Run operational drift and performance checks:

```powershell
python scripts/run_drift.py
python scripts/benchmark.py
```

Outputs are written to `reports/drift/`, `reports/benchmarks/`, and `artifacts/metrics.json`.

Run the quality gate:

```powershell
ruff check src scripts dashboard tests
black --check src scripts dashboard tests
mypy src
pytest -q
```

Testing architecture and fixture policy are documented in [docs/TESTING.md](docs/TESTING.md). Unit tests use synthetic data and temporary artifacts; integration and E2E tests exercise the real API and authentication implementation.

Build and run the production container:

```powershell
docker build --target production -t enterprise-fraud-detection:1.0.0 .
docker compose up --build
```

Training configuration lives under `training` in `configs/config.yaml`. Set `smote_enabled`, split sizes, search strategy, selection metric, feature lists, and model search spaces there. Each run creates a new `models/vN/` and `artifacts/vN/` directory and never overwrites an existing version.

Outputs are written to `reports/`, `reports/figures/`, and `logs/`. The dataset always belongs in `data/raw/`.

## Project Roadmap

1. **Phase 1:** Foundation, configuration, logging, dataset management, and EDA
2. **Phase 2:** Feature engineering, preprocessing, model training, tuning, comparison, and versioning
3. **Phase 3:** Evaluation, threshold optimization, explainability, error analysis, model cards, and experiment tracking
4. **Phase 4:** FastAPI service, authentication, prediction workflows, and dashboard
5. **Phase 5:** Docker, automated testing, CI quality checks, monitoring, drift detection, security, benchmarking, and release documentation

## Engineering Principles

- Configuration owns paths and runtime settings.
- Modules receive settings explicitly rather than relying on global state.
- Raw data is immutable input; generated outputs are separated by directory.
- Phase boundaries remain stable as later capabilities are added.
