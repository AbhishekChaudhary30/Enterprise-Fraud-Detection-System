# Enterprise Fraud Intelligence Platform

A production-grade, end-to-end Machine Learning platform for detecting and managing fraudulent transactions. This system upgrades standard ML model training into a full-scale operational intelligence platform with risk scoring, explainable AI (SHAP), workflow management, and real-time monitoring.

## 🌟 Key Features

### Intelligence Engine
- **Risk Scoring & Tiers**: Converts raw ML probabilities into operational risk scores (0-100) and actionable tiers (LOW / MEDIUM / HIGH).
- **Explainable AI (SHAP)**: Every prediction generates a real-time, feature-level SHAP explanation (e.g., *Feature X increased fraud risk by +0.12*).
- **Automated Workflow**: High-risk transactions automatically trigger an investigation workflow for human review.

### Platform Architecture
- **Stateful Persistence**: PostgreSQL-backed registry for predictions, batch jobs, model versions, and investigations.
- **Modern Frontend**: React + TypeScript + Vite + Tailwind CSS dashboard with KPI metrics, charts, and interactive risk gauges.
- **Robust API**: FastAPI backend with JWT authentication, security headers, rate limiting, and CORS.
- **Dockerized**: Multi-container setup (Database, Backend API, Frontend Nginx) via `docker-compose`.

### ML Lifecycle (Phase 1-3)
- **Data & Training**: Automated dataset validation, EDA reporting, feature engineering, and robust model comparison (Logistic Regression, Random Forest, XGBoost, LightGBM, CatBoost).
- **Evaluation**: Optimized threshold calculation, probability calibration, and automated model card generation.
- **Model Registry**: Disk and database-backed model versioning with champion/challenger tracking.

## 📂 Architecture

```text
├── frontend/               # React + TypeScript + Vite UI
├── src/
│   ├── api/                # FastAPI application, routers, schemas
│   ├── auth/               # JWT authentication & RBAC
│   ├── database/           # SQLAlchemy ORM models & CRUD repositories
│   ├── features/           # Sklearn-compatible feature engineering
│   ├── modeling/           # Training orchestration & model factory
│   └── serving/            # Prediction service & SHAP explainers
├── scripts/                # CLI entrypoints (train, evaluate, api)
├── configs/                # YAML configuration definitions
├── docker-compose.yml      # Infrastructure definition
└── pyproject.toml          # Project dependencies (FastAPI, SQLAlchemy, XGBoost, etc.)
```

## 🚀 Quick Start (Docker)

The fastest way to run the entire platform is using Docker Compose.

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env to set secure JWT_SECRET and ADMIN_PASSWORD
   ```

2. **Start the Platform**
   ```bash
   docker-compose up --build -d
   ```

3. **Access Services**
   - **Dashboard**: `http://localhost:3000`
   - **API Docs**: `http://localhost:8000/docs`

4. **Login**
   - **Username**: `admin`
   - **Password**: `admin-dev-password` (or whatever you set in `.env`)

## 🛠️ Local Development Setup

### 1. Backend Setup
Python 3.12 is required.

```powershell
# Create and activate virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 2. Run the ML Pipeline (Optional)
If you want to train a new model from scratch:

```powershell
python scripts/download_dataset.py
python scripts/train.py
python scripts/evaluate.py
```

### 3. Start Backend Services
Using SQLite for local development:
```powershell
python scripts/start_api.py
```
*API runs at `http://localhost:8000/api/v1`*

### 4. Start Frontend
In a new terminal:
```powershell
cd frontend
npm install
npm run dev
```
*Frontend runs at `http://localhost:5173`*

## 🧪 Testing

The repository maintains strict quality gates including unit, integration, and end-to-end tests.

```powershell
# Run the test suite
pytest tests/ -v

# Run formatters and linters
ruff check src scripts tests
black --check src scripts tests
mypy src
```

## 📝 User Workflows

### 1. Single Transaction Scoring
Navigate to **Predict**. Input transaction features (via Form or JSON). The system returns the fraud probability, risk tier (LOW/MEDIUM/HIGH), execution latency, and a SHAP feature contribution waterfall chart.

### 2. Batch Processing
Navigate to **Batch**. Upload a CSV of transactions. The system processes them in bulk, stores a batch summary job in the database, and provides a downloadable CSV containing the original data appended with prediction IDs and risk scores.

### 3. Fraud Investigation
Navigate to **Investigations**. View auto-generated cases for High-Risk transactions. Update the status through the workflow (`NEW` -> `UNDER REVIEW` -> `CONFIRMED FRAUD` / `FALSE POSITIVE`).

### 4. Model Registry
Navigate to **Models**. View the currently active Champion model, its evaluation metrics (PR-AUC, F1, Recall), and compare historical training runs.
