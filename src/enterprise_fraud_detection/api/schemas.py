"""FastAPI request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginResponse(BaseModel):
    """JWT login response."""

    access_token: str
    token_type: str = "bearer"
    role: str


class PredictionRequest(BaseModel):
    """Single transaction feature payload."""

    features: dict[str, Any] = Field(min_length=1)
    version: str | None = None
    threshold: float | None = Field(default=None, gt=0, lt=1)


class BatchPredictionRequest(BaseModel):
    """Batch transaction feature payload."""

    records: list[dict[str, Any]] = Field(min_length=1)
    version: str | None = None
    threshold: float | None = Field(default=None, gt=0, lt=1)


class PredictionResponse(BaseModel):
    """Single prediction response."""

    prediction_id: str
    prediction_timestamp: str
    model_version: str
    predicted_label: int
    fraud_probability: float
    confidence_score: float
    threshold: float
    input_reference: str
    execution_time_ms: float


class ErrorResponse(BaseModel):
    """Consistent API error response."""

    detail: str
