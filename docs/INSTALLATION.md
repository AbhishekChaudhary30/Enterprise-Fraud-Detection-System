# Installation Guide

## Local

Use Python 3.12 and create an isolated environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set `JWT_SECRET` and `ADMIN_PASSWORD` in `.env` before starting the API.

## First Run

```powershell
python scripts/train.py
python scripts/evaluate.py
python scripts/generate_sample_csv.py
python scripts/start_api.py
```

Run the dashboard in a second terminal with `python scripts/start_dashboard.py`.
