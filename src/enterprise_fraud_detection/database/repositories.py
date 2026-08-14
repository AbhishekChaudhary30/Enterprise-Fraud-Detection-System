"""Database repository layer for CRUD operations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from enterprise_fraud_detection.database.models import (
    BatchJob,
    Investigation,
    ModelVersion,
    PredictionRecord,
)


class PredictionRepository:
    """CRUD operations for prediction records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: dict[str, Any]) -> PredictionRecord:
        """Insert a new prediction record."""
        record = PredictionRecord(
            prediction_id=data["prediction_id"],
            prediction_timestamp=datetime.fromisoformat(data["prediction_timestamp"]),
            model_version=data["model_version"],
            prediction_type=data.get("prediction_type", "single"),
            fraud_probability=data["fraud_probability"],
            risk_score=data["risk_score"],
            risk_level=data["risk_level"],
            decision=data["decision"],
            predicted_label=data["predicted_label"],
            threshold=data["threshold"],
            execution_time_ms=data.get("execution_time_ms"),
            input_reference=data.get("input_reference"),
            features_json=json.dumps(data.get("features"), default=str) if data.get("features") else None,
            explanation_json=json.dumps(data.get("explanation"), default=str) if data.get("explanation") else None,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, prediction_id: str) -> PredictionRecord | None:
        return self.session.query(PredictionRecord).filter_by(prediction_id=prediction_id).first()

    def list_recent(self, limit: int = 100, risk_level: str | None = None) -> list[PredictionRecord]:
        query = self.session.query(PredictionRecord)
        if risk_level:
            query = query.filter_by(risk_level=risk_level)
        return list(query.order_by(desc(PredictionRecord.prediction_timestamp)).limit(limit).all())

    def count_by_risk_level(self) -> dict[str, int]:
        results = (
            self.session.query(PredictionRecord.risk_level, func.count())
            .group_by(PredictionRecord.risk_level)
            .all()
        )
        return {level: count for level, count in results}

    def count_total(self) -> int:
        return self.session.query(func.count(PredictionRecord.id)).scalar() or 0

    def count_fraud(self) -> int:
        return (
            self.session.query(func.count(PredictionRecord.id))
            .filter(PredictionRecord.predicted_label == 1)
            .scalar()
            or 0
        )

    def avg_probability(self) -> float:
        result = self.session.query(func.avg(PredictionRecord.fraud_probability)).scalar()
        return float(result) if result else 0.0


class InvestigationRepository:
    """CRUD operations for fraud investigations."""

    VALID_STATUSES = {"NEW", "UNDER_REVIEW", "CONFIRMED_FRAUD", "FALSE_POSITIVE", "RESOLVED"}

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, prediction_id: str, priority: str = "MEDIUM") -> Investigation:
        investigation = Investigation(
            prediction_id=prediction_id,
            status="NEW",
            priority=priority,
        )
        self.session.add(investigation)
        self.session.flush()
        return investigation

    def get_by_id(self, investigation_id: int) -> Investigation | None:
        return self.session.query(Investigation).filter_by(id=investigation_id).first()

    def get_by_prediction_id(self, prediction_id: str) -> Investigation | None:
        return self.session.query(Investigation).filter_by(prediction_id=prediction_id).first()

    def list_all(
        self, limit: int = 100, status: str | None = None
    ) -> list[Investigation]:
        query = self.session.query(Investigation)
        if status:
            query = query.filter_by(status=status)
        return list(query.order_by(desc(Investigation.created_at)).limit(limit).all())

    def update_status(
        self, investigation_id: int, status: str, notes: str | None = None, assigned_to: str | None = None
    ) -> Investigation | None:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Valid: {sorted(self.VALID_STATUSES)}")
        investigation = self.get_by_id(investigation_id)
        if investigation is None:
            return None
        investigation.status = status
        investigation.updated_at = datetime.now(UTC)
        if notes is not None:
            investigation.notes = notes
        if assigned_to is not None:
            investigation.assigned_to = assigned_to
        self.session.flush()
        return investigation

    def count_by_status(self) -> dict[str, int]:
        results = (
            self.session.query(Investigation.status, func.count())
            .group_by(Investigation.status)
            .all()
        )
        return {status: count for status, count in results}


class ModelVersionRepository:
    """CRUD operations for model version registry."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def register(self, version: str, algorithm: str, metrics: dict[str, Any] | None = None,
                 threshold: float | None = None, row_count: int | None = None,
                 training_duration: float | None = None, status: str = "archived") -> ModelVersion:
        record = ModelVersion(
            version=version,
            algorithm=algorithm,
            status=status,
            metrics_json=json.dumps(metrics, default=str) if metrics else None,
            threshold=threshold,
            row_count=row_count,
            training_duration_seconds=training_duration,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_champion(self) -> ModelVersion | None:
        return self.session.query(ModelVersion).filter_by(status="champion").first()

    def list_all(self) -> list[ModelVersion]:
        return list(self.session.query(ModelVersion).order_by(desc(ModelVersion.created_at)).all())

    def set_champion(self, version: str) -> ModelVersion | None:
        # Demote current champion
        current = self.get_champion()
        if current:
            current.status = "archived"
        # Promote new champion
        model = self.session.query(ModelVersion).filter_by(version=version).first()
        if model:
            model.status = "champion"
            self.session.flush()
        return model


class BatchJobRepository:
    """CRUD operations for batch prediction jobs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: dict[str, Any]) -> BatchJob:
        job = BatchJob(
            batch_id=data["prediction_id"],
            total_rows=data["total_transactions"],
            fraud_count=data["fraud_predictions"],
            high_risk_count=data.get("risk_distribution", {}).get("high", 0),
            medium_risk_count=data.get("risk_distribution", {}).get("medium", 0),
            low_risk_count=data.get("risk_distribution", {}).get("low", 0),
            model_version=data["model_version"],
            file_path=data.get("output_path"),
            execution_time_ms=data.get("execution_time_ms"),
        )
        self.session.add(job)
        self.session.flush()
        return job

    def list_recent(self, limit: int = 50) -> list[BatchJob]:
        return list(self.session.query(BatchJob).order_by(desc(BatchJob.created_at)).limit(limit).all())
