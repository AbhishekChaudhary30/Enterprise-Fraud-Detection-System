# Repository Instructions

- Keep the `src/enterprise_fraud_detection` package layout stable across phases.
- Use `Settings` from `enterprise_fraud_detection.config` for all paths and runtime configuration.
- Use `pathlib.Path`, type hints, docstrings, and focused modules.
- Keep Phase 1 limited to configuration, logging, dataset management, and EDA.
- Do not add model training, prediction, FastAPI, dashboard, Docker, monitoring, or explainability until their planned phases.
- Do not commit `.env`, raw datasets, logs, generated reports, model files, or runtime artifacts.
