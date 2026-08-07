# Repository Instructions

- Keep the `src/enterprise_fraud_detection` package layout stable across phases.
- Use `Settings` from `enterprise_fraud_detection.config` for all paths and runtime configuration.
- Use `pathlib.Path`, type hints, docstrings, and focused modules.
- Keep the current Phase 2 scope limited to preprocessing, feature engineering, model training, tuning, comparison, and versioning.
- Do not add prediction APIs, FastAPI, dashboard, Docker, monitoring, or explainability until their planned phases.
- Do not commit `.env`, raw datasets, logs, generated reports, model files, or runtime artifacts.
