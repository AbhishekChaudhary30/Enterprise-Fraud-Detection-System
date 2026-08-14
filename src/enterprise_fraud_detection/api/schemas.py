"""FastAPI request and response schemas for the fraud intelligence platform."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# --- Authentication ---


class LoginResponse(BaseModel):
    """JWT login response."""

    access_token: str
    token_type: str = "bearer"
    role: str


class RegisterRequest(BaseModel):
    """User registration payload."""
    
    username: str
    password: str


# --- Predictions ---


class PredictionRequest(BaseModel):
    """Single transaction feature payload."""

    features: dict[str, Any] = Field(min_length=1)
    version: str | None = None
    threshold: float | None = Field(default=None, gt=0, lt=1)


class ExplanationItem(BaseModel):
    """Single feature contribution from SHAP."""

    feature: str
    shap_value: float
    direction: str


class PredictionResponse(BaseModel):
    """Single prediction response with risk scoring and explanation."""

    prediction_id: str
    prediction_timestamp: str
    model_version: str
    predicted_label: int
    fraud_probability: float
    risk_score: int
    risk_level: str
    decision: str
    threshold: float
    input_reference: str
    execution_time_ms: float
    explanation: list[ExplanationItem] = []


class BatchPredictionRequest(BaseModel):
    """Batch transaction feature payload."""

    records: list[dict[str, Any]] = Field(min_length=1)
    version: str | None = None
    threshold: float | None = Field(default=None, gt=0, lt=1)


class RiskDistribution(BaseModel):
    """Risk level distribution counts."""

    low: int = 0
    medium: int = 0
    high: int = 0


class BatchSummary(BaseModel):
    """Batch prediction summary."""

    prediction_id: str
    prediction_timestamp: str
    model_version: str
    total_transactions: int
    fraud_predictions: int
    risk_distribution: RiskDistribution
    execution_time_ms: float


# --- Investigations ---


class InvestigationCreate(BaseModel):
    """Create a new investigation for a prediction."""

    prediction_id: str
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")


class InvestigationUpdate(BaseModel):
    """Update an investigation's status."""

    status: str = Field(pattern="^(NEW|UNDER_REVIEW|CONFIRMED_FRAUD|FALSE_POSITIVE|RESOLVED)$")
    notes: str | None = None
    assigned_to: str | None = None


class InvestigationResponse(BaseModel):
    """Investigation record response."""

    id: int
    prediction_id: str
    status: str
    priority: str
    assigned_to: str | None
    notes: str | None
    created_at: str
    updated_at: str


# --- Dashboard ---


class DashboardStats(BaseModel):
    """Dashboard KPI statistics."""

    total_predictions: int
    fraud_detected: int
    fraud_rate: float
    risk_distribution: RiskDistribution
    model_version: str
    model_algorithm: str
    avg_probability: float
    investigation_counts: dict[str, int] = {}


# --- Model ---


class ModelMetricsResponse(BaseModel):
    """Model evaluation metrics."""

    version: str
    algorithm: str
    status: str
    metrics: dict[str, float] = {}
    threshold: float | None = None
    training_duration_seconds: float | None = None
    row_count: int | None = None


# --- Monitoring ---


class MonitoringOverview(BaseModel):
    """System monitoring overview."""

    prediction_volume: int
    fraud_prediction_rate: float
    risk_distribution: RiskDistribution
    model_version: str
    model_loaded: bool
    avg_latency_ms: float
    error_count: int
    uptime_seconds: float


# --- Errors ---


class ErrorResponse(BaseModel):
    """Consistent API error response."""

    detail: str
