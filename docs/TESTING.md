# Testing Guide

The suite is divided by execution boundary:

- `tests/unit/`: isolated components. These tests use only synthetic data and pytest temporary directories. They do not read the Kaggle dataset, repository reports, committed models, or prior execution state.
- `tests/integration/`: real FastAPI routes, authentication, prediction service, model loader, and history working together with temporary versioned artifacts.
- `tests/e2e/`: public client workflows through the compatibility and versioned API contracts.

## Commands

```powershell
pytest -m unit -q
pytest -m integration -q
pytest -m e2e -q
pytest -q
```

The shared fixtures in `tests/conftest.py` create deterministic `Settings`, synthetic feature rows, temporary model versions, and an isolated API service graph. External resources are not mocked; only the filesystem location is redirected to pytest's temporary directory.

GitHub Actions runs the quality gate on Ubuntu and Windows with `APP_ENVIRONMENT=test` and a fixed `PYTHONHASHSEED`. No test downloads data, trains a production model, or depends on a previous run.
