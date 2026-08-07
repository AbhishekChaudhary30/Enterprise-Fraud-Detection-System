# Architecture

The system is organized around explicit ownership boundaries:

- `config`: YAML and environment-backed runtime settings.
- `data`: raw dataset acquisition and validation.
- `features`: reusable preprocessing and feature engineering.
- `modeling`: Phase 2 training, comparison, and versioning.
- `evaluation`: Phase 3 metrics, plots, SHAP, reports, and experiment history.
- `serving`: model loading, prediction, CSV workflows, and history.
- `api`: FastAPI composition, dependencies, schemas, and routers.
- `auth`: JWT authentication and role checks.
- `monitoring`: runtime metrics, security middleware, and drift detection.
- `dashboard`: Streamlit user interface over the API and Phase 3 outputs.

The API never trains models. It loads immutable versioned artifacts and routes all scoring through the persisted Phase 2 pipeline.
