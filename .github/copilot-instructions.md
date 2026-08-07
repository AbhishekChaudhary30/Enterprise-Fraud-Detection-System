# Repository Instructions

- Keep the `src/enterprise_fraud_detection` package layout stable across phases.
- Use `Settings` from `enterprise_fraud_detection.config` for all paths and runtime configuration.
- Use `pathlib.Path`, type hints, docstrings, and focused modules.
- Preserve the existing Phase 1-5 package boundaries and public APIs.
- Keep configuration and paths owned by `Settings`; do not duplicate runtime configuration.
- Phase 5 includes packaging, tests, CI quality checks, monitoring, drift detection, security hardening, benchmarking, and documentation.
- Do not add unrelated cloud deployment or deployment-specific automation.
- Do not commit `.env`, raw datasets, logs, generated reports, model files, or runtime artifacts.
