"""Protected prediction endpoints with database persistence."""

from __future__ import annotations

import io
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from enterprise_fraud_detection.api.dependencies import current_user, service
from enterprise_fraud_detection.api.schemas import (
    BatchPredictionRequest,
    PredictionRequest,
    PredictionResponse,
)
from enterprise_fraud_detection.database.connection import get_db
from enterprise_fraud_detection.database.repositories import (
    BatchJobRepository,
    InvestigationRepository,
    PredictionRepository,
)
from enterprise_fraud_detection.serving.prediction import PredictionService

router = APIRouter()
CSV_FILE = File(...)


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    payload: PredictionRequest,
    request: Request,
    prediction_service: Annotated[PredictionService, Depends(service)],
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Score one transaction with risk scoring and SHAP explanation."""
    del user
    response = prediction_service.predict_one(payload.features, payload.version, payload.threshold)
    request.app.state.metrics.observe_prediction()

    # Persist to database
    try:
        with get_db() as db:
            repo = PredictionRepository(db)
            record = repo.create({**response, "features": payload.features})

            # Auto-create investigation for HIGH risk predictions
            if response["risk_level"] == "HIGH":
                inv_repo = InvestigationRepository(db)
                inv_repo.create(response["prediction_id"], priority="HIGH")
            db.commit()
    except Exception:
        pass  # Don't fail predictions if DB write fails

    return response


@router.post("/predict/batch")
async def predict_batch(
    payload: BatchPredictionRequest,
    request: Request,
    prediction_service: Annotated[PredictionService, Depends(service)],
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Score a JSON batch and return prediction rows with risk scoring."""
    del user
    frame = pd.DataFrame(payload.records)
    output, summary = prediction_service.predict_batch(
        frame, payload.version, payload.threshold, input_reference="json_batch"
    )
    request.app.state.metrics.observe_prediction(len(output), batch=True)

    # Persist batch job to database
    try:
        with get_db() as db:
            repo = BatchJobRepository(db)
            repo.create(summary)
            db.commit()
    except Exception:
        pass

    return {"summary": summary, "predictions": output.to_dict(orient="records")}


@router.post("/upload")
async def upload_csv(
    request: Request,
    prediction_service: Annotated[PredictionService, Depends(service)],
    user: Annotated[dict[str, str], Depends(current_user)],
    file: UploadFile = CSV_FILE,
) -> StreamingResponse:
    """Validate an uploaded CSV, score it, and return a downloadable CSV."""
    del user
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only CSV uploads are supported")
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="File size exceeds 50MB limit")
    try:
        frame = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid CSV file: {exc}") from exc
    frame = prediction_service.validate_csv(frame, prediction_service.settings.dataset.target_column)
    output, summary = prediction_service.predict_batch(frame, input_reference=file.filename)
    request.app.state.metrics.observe_prediction(len(output), batch=True)

    # Persist batch job to database
    try:
        with get_db() as db:
            repo = BatchJobRepository(db)
            repo.create(summary)
            db.commit()
    except Exception:
        pass

    stream = io.StringIO()
    output.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="predictions_{file.filename}"'},
    )


@router.get("/history")
async def history(
    prediction_service: Annotated[PredictionService, Depends(service)],
    user: Annotated[dict[str, str], Depends(current_user)],
    limit: int = 100,
) -> dict[str, Any]:
    """Return recent prediction history from database."""
    del user
    if not 1 <= limit <= 1000:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 1000")

    # Try database first, fall back to file-based history
    try:
        with get_db() as db:
            repo = PredictionRepository(db)
            records = repo.list_recent(limit=limit)
            if records:
                return {
                    "history": [
                        {
                            "prediction_id": r.prediction_id,
                            "prediction_timestamp": r.prediction_timestamp.isoformat(),
                            "model_version": r.model_version,
                            "fraud_probability": r.fraud_probability,
                            "risk_score": r.risk_score,
                            "risk_level": r.risk_level,
                            "decision": r.decision,
                            "predicted_label": r.predicted_label,
                            "execution_time_ms": r.execution_time_ms,
                        }
                        for r in records
                    ]
                }
    except Exception:
        pass

    return {"history": prediction_service.history(limit)}
