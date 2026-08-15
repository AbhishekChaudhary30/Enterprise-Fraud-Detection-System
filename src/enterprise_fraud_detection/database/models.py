"""SQLAlchemy ORM models for the fraud intelligence platform."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class User(Base):
    """Registered user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )


class PredictionRecord(Base):
    """Persisted prediction with risk scoring and explanation metadata."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    prediction_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    model_version: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    prediction_type: Mapped[str] = mapped_column(String(20), default="single", nullable=False)
    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(10), nullable=False)
    predicted_label: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    input_reference: Mapped[str] = mapped_column(String(255), nullable=True)
    features_json: Mapped[str] = mapped_column(Text, nullable=True)
    explanation_json: Mapped[str] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )


class Investigation(Base):
    """Fraud investigation workflow record linked to a prediction."""

    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    prediction_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="NEW", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(10), default="MEDIUM", nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ModelVersion(Base):
    """Registered model version with metrics and status."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="archived", nullable=False)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, nullable=True)
    training_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )


class BatchJob(Base):
    """Batch prediction job tracking record."""

    __tablename__ = "batch_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    batch_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    fraud_count: Mapped[int] = mapped_column(Integer, nullable=False)
    high_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
