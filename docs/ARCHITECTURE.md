# Architecture: Enterprise Fraud Intelligence

## Overview

The Enterprise Fraud Intelligence Platform is a state-of-the-art ML system transitioning standard inference into operational business value.

## Core Components

### 1. Persistence Layer (Database)
- **Technology**: PostgreSQL (via SQLAlchemy ORM).
- **Purpose**: We moved away from stateless file-based JSONL logging to a robust RDBMS.
- **Entities**:
  - `PredictionRecord`: Stores every API request, the model's inference probability, the computed risk score/tier, execution latency, and the full SHAP explanation (JSON blob).
  - `Investigation`: Linked to predictions. Tracks the operational workflow of reviewing high-risk transactions.
  - `BatchJob`: Tracks large-scale CSV processing metrics.
  - `ModelVersion`: Registers trained models, their hyperparameters, and evaluation metrics for champion/challenger governance.

### 2. ML Serving Layer
- **RiskClassifier**: Abstracted out of the raw model. The ML model outputs a pure probability (0.0 to 1.0). The classifier converts this into a Business Risk Tier (`LOW`, `MEDIUM`, `HIGH`) based on configured thresholds.
- **PredictionExplainer**: Wraps `shap.TreeExplainer`. It generates real-time feature contribution analysis for transparency, avoiding "black box" decisions.

### 3. API Layer
- **Technology**: FastAPI.
- **Design**: Protected by JWT authentication. Provides RESTful endpoints for single predictions, batch uploads, investigations CRUD, and monitoring metrics.

### 4. Frontend Layer
- **Technology**: React 18, TypeScript, Vite, Tailwind CSS (v4), Recharts.
- **Purpose**: Provides the Security Operations Center (SOC) with a dynamic, glassmorphic dashboard to monitor KPIs, review SHAP charts, and action investigations.

## Request Lifecycle
1. **Client** (Frontend or API consumer) sends a transaction payload (`{"Amount": 20.0, "V1": -1.2...}`).
2. **FastAPI** routes the request to `PredictionService` after validating JWT and Rate Limits.
3. **ModelLoader** fetches the champion XGBoost/LightGBM artifact from memory.
4. **PredictionExplainer** computes SHAP values.
5. **RiskClassifier** calculates Risk Score & Tier.
6. **PredictionRepository** persists the result to PostgreSQL.
7. If Risk == HIGH, **InvestigationRepository** auto-creates a case.
8. API returns the full composite payload back to the client.
