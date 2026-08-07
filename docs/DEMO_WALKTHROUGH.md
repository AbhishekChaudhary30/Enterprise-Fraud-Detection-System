# Demo Walkthrough

1. Copy `.env.example` to `.env` and set credentials.
2. Start the API with `python scripts/start_api.py`.
3. Open `/docs`, log in, and call `/api/v1/models/latest`.
4. Use `data/external/sample_transactions.csv` with the upload route.
5. Open the dashboard with `python scripts/start_dashboard.py`.
6. Review metrics, plots, SHAP outputs, prediction history, and model versions.
7. Run `python scripts/benchmark.py` and `python scripts/run_drift.py` to show operational checks.
