"""Protected prediction endpoints."""

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
    """Score one transaction through the latest or requested model version."""
    del user
    response = prediction_service.predict_one(payload.features, payload.version, payload.threshold)
    request.app.state.metrics.observe_prediction()
    return response


@router.post("/predict/batch")
async def predict_batch(
    payload: BatchPredictionRequest,
    request: Request,
    prediction_service: Annotated[PredictionService, Depends(service)],
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Score a JSON batch and return prediction rows."""
    del user
    frame = pd.DataFrame(payload.records)
    output, details = prediction_service.predict_batch(
        frame, payload.version, payload.threshold, input_reference="json_batch"
    )
    request.app.state.metrics.observe_prediction(len(output), batch=True)
    return {"metadata": details, "predictions": output.to_dict(orient="records")}


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
    frame = prediction_service.validate_csv(
        pd.read_csv(io.BytesIO(content)), prediction_service.settings.dataset.target_column
    )
    output, _ = prediction_service.predict_batch(frame, input_reference=file.filename)
    request.app.state.metrics.observe_prediction(len(output), batch=True)
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
    """Return recent prediction history."""
    del user
    if not 1 <= limit <= 1000:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 1000")
    return {"history": prediction_service.history(limit)}
