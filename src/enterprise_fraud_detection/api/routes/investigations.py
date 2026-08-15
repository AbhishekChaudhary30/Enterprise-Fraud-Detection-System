"""Investigation workflow endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from enterprise_fraud_detection.api.dependencies import current_user
from enterprise_fraud_detection.api.schemas import (
    InvestigationCreate,
    InvestigationResponse,
    InvestigationUpdate,
)
from enterprise_fraud_detection.database.connection import SessionLocal
from enterprise_fraud_detection.database.repositories import (
    InvestigationRepository,
    PredictionRepository,
)

router = APIRouter()


@router.get("/investigations")
async def list_investigations(
    user: Annotated[dict[str, str], Depends(current_user)],
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    """List investigations with optional status filter."""
    del user
    with SessionLocal() as db:
        user_id = int(user["user_id"]) if "user_id" in user else None
        repo = InvestigationRepository(db, user_id=user_id)
        investigations = repo.list_all(limit=limit, status=status)
        counts = repo.count_by_status()
        return {
            "investigations": [
                InvestigationResponse(
                    id=inv.id,
                    prediction_id=inv.prediction_id,
                    status=inv.status,
                    priority=inv.priority,
                    assigned_to=inv.assigned_to,
                    notes=inv.notes,
                    created_at=inv.created_at.isoformat() if inv.created_at else "",
                    updated_at=inv.updated_at.isoformat() if inv.updated_at else "",
                ).model_dump()
                for inv in investigations
            ],
            "status_counts": counts,
        }


@router.post("/investigations")
async def create_investigation(
    payload: InvestigationCreate,
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Create an investigation for a high-risk prediction."""
    del user
    with SessionLocal() as db:
        user_id = int(user["user_id"]) if "user_id" in user else None
        pred_repo = PredictionRepository(db, user_id=user_id)
        prediction = pred_repo.get_by_id(payload.prediction_id)
        if prediction is None:
            raise HTTPException(status_code=404, detail="Prediction not found")
        inv_repo = InvestigationRepository(db, user_id=user_id)
        existing = inv_repo.get_by_prediction_id(payload.prediction_id)
        if existing:
            raise HTTPException(
                status_code=409, detail="Investigation already exists for this prediction"
            )
        investigation = inv_repo.create(payload.prediction_id, payload.priority)
        db.commit()
        return {
            "id": investigation.id,
            "prediction_id": investigation.prediction_id,
            "status": investigation.status,
            "priority": investigation.priority,
        }


@router.get("/investigations/{investigation_id}")
async def get_investigation(
    investigation_id: int,
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Get a single investigation with linked prediction details."""
    del user
    with SessionLocal() as db:
        user_id = int(user["user_id"]) if "user_id" in user else None
        inv_repo = InvestigationRepository(db, user_id=user_id)
        investigation = inv_repo.get_by_id(investigation_id)
        if investigation is None:
            raise HTTPException(status_code=404, detail="Investigation not found")
        pred_repo = PredictionRepository(db, user_id=user_id)
        prediction = pred_repo.get_by_id(investigation.prediction_id)
        pred_data = None
        if prediction:
            pred_data = {
                "prediction_id": prediction.prediction_id,
                "fraud_probability": prediction.fraud_probability,
                "risk_score": prediction.risk_score,
                "risk_level": prediction.risk_level,
                "decision": prediction.decision,
                "model_version": prediction.model_version,
                "prediction_timestamp": prediction.prediction_timestamp.isoformat(),
                "explanation": prediction.explanation_json,
            }
        return {
            "investigation": InvestigationResponse(
                id=investigation.id,
                prediction_id=investigation.prediction_id,
                status=investigation.status,
                priority=investigation.priority,
                assigned_to=investigation.assigned_to,
                notes=investigation.notes,
                created_at=investigation.created_at.isoformat() if investigation.created_at else "",
                updated_at=investigation.updated_at.isoformat() if investigation.updated_at else "",
            ).model_dump(),
            "prediction": pred_data,
        }


@router.patch("/investigations/{investigation_id}")
async def update_investigation(
    investigation_id: int,
    payload: InvestigationUpdate,
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Update an investigation status in the workflow."""
    del user
    with SessionLocal() as db:
        user_id = int(user["user_id"]) if "user_id" in user else None
        repo = InvestigationRepository(db, user_id=user_id)
        investigation = repo.update_status(
            investigation_id, payload.status, payload.notes, payload.assigned_to
        )
        if investigation is None:
            raise HTTPException(status_code=404, detail="Investigation not found")
        db.commit()
        return {
            "id": investigation.id,
            "status": investigation.status,
            "updated_at": investigation.updated_at.isoformat() if investigation.updated_at else "",
        }
