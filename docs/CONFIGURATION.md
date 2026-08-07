# Configuration Guide

All runtime behavior is configured through `configs/config.yaml`. Relative paths resolve from the project root. `.env` supplies secrets and deployment overrides.

Important Phase 5 values:

- `serving`: API host/port, JWT behavior, threshold, and prediction storage.
- `production`: environment, rate limits, request ID header, metrics, drift, and benchmark destinations.
- `evaluation`: Phase 3 report locations and threshold strategy.

Never commit `.env`, credentials, model files, raw data, logs, or generated runtime artifacts.
