# Project Structure Guide

```text
configs/                 Runtime YAML
src/enterprise_fraud_detection/
  config/               Settings
  data/                 Dataset utilities
  features/             Preprocessing and features
  modeling/             Training and versioning
  evaluation/           Evaluation and SHAP
  serving/              Loading and predictions
  auth/                 JWT security
  api/                  FastAPI service
  monitoring/           Metrics and drift
 dashboard/             Streamlit UI
 scripts/               Operational commands
tests/                  Automated tests
docs/                   Project documentation
models/                 Immutable model versions
artifacts/              Runtime artifacts and history
reports/                Evaluation, drift, and benchmark outputs
```
