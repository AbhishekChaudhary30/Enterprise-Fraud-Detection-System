"""Monitoring and dashboard statistics endpoints."""

from __future__ import annotations

import json
import time
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from enterprise_fraud_detection.api.dependencies import current_user
from enterprise_fraud_detection.database.connection import get_db
from enterprise_fraud_detection.database.repositories import (
    BatchJobRepository,
    InvestigationRepository,
    PredictionRepository,
)

router = APIRouter()

_START_TIME = time.time()


@router.get("/dashboard/stats")
async def dashboard_stats(
    request: Request,
    user: Annotated[dict[str, str], Depends(current_user)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Aggregated KPI statistics for the dashboard."""
    loader = request.app.state.loader
    try:
        bundle = loader.load()
        model_version = bundle.version
        model_algorithm = bundle.metadata.get("selected_model", "unknown")
    except Exception:
        model_version = "None loaded"
        model_algorithm = "N/A"

    user_id = int(user["user_id"]) if "user_id" in user else None
    pred_repo = PredictionRepository(db, user_id=user_id)
    inv_repo = InvestigationRepository(db, user_id=user_id)
    total = pred_repo.count_total()
    fraud = pred_repo.count_fraud()
    risk_dist = pred_repo.count_by_risk_level()
    avg_prob = pred_repo.avg_probability()
    inv_counts = inv_repo.count_by_status()

    # Load evaluation metrics from bundle metadata
    metrics: dict[str, float] = {}
    try:
        if "bundle" in locals() and hasattr(bundle, "metadata"):
            comparisons = bundle.metadata.get("comparisons", [])
            for comp in comparisons:
                if comp.get("model_name") == model_algorithm and comp.get("test_metrics"):
                    metrics = comp["test_metrics"]
                    break
    except Exception:
        pass

    return {
        "total_predictions": total,
        "fraud_detected": fraud,
        "fraud_rate": round(fraud / total, 4) if total > 0 else 0.0,
        "risk_distribution": {
            "low": risk_dist.get("LOW", 0),
            "medium": risk_dist.get("MEDIUM", 0),
            "high": risk_dist.get("HIGH", 0),
        },
        "model_version": model_version,
        "model_algorithm": model_algorithm,
        "avg_probability": round(avg_prob, 6),
        "investigation_counts": inv_counts,
        "model_metrics": metrics,
    }


@router.post("/dashboard/reset")
async def dashboard_reset(
    user: Annotated[dict[str, str], Depends(current_user)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reset the dashboard by archiving all current predictions."""
    user_id = int(user["user_id"]) if "user_id" in user else None
    pred_repo = PredictionRepository(db, user_id=user_id)
    archived_count = pred_repo.archive_all()
    return {"status": "success", "archived_count": archived_count}


@router.get("/dashboard/recent")
async def dashboard_recent(
    user: Annotated[dict[str, str], Depends(current_user)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Recent predictions for the dashboard table."""
    user_id = int(user["user_id"]) if "user_id" in user else None
    pred_repo = PredictionRepository(db, user_id=user_id)
    recent = pred_repo.list_recent(limit=20)
    return {
            "predictions": [
                {
                    "prediction_id": p.prediction_id,
                    "prediction_timestamp": p.prediction_timestamp.isoformat(),
                    "fraud_probability": p.fraud_probability,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "decision": p.decision,
                    "model_version": p.model_version,
                }
                for p in recent
            ]
        }


@router.get("/dashboard/high-risk")
async def dashboard_high_risk(
    user: Annotated[dict[str, str], Depends(current_user)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """High-risk predictions requiring attention."""
    user_id = int(user["user_id"]) if "user_id" in user else None
    pred_repo = PredictionRepository(db, user_id=user_id)
    high_risk = pred_repo.list_recent(limit=20, risk_level="HIGH")
    return {
            "predictions": [
                {
                    "prediction_id": p.prediction_id,
                    "prediction_timestamp": p.prediction_timestamp.isoformat(),
                    "fraud_probability": p.fraud_probability,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "decision": p.decision,
                    "model_version": p.model_version,
                    "input_reference": p.input_reference,
                }
                for p in high_risk
            ]
        }


@router.get("/monitoring/overview")
async def monitoring_overview(
    request: Request,
    user: Annotated[dict[str, str], Depends(current_user)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """System monitoring overview — prediction volume, model health, latency."""
    metrics_snapshot = cast(dict[str, Any], request.app.state.metrics.snapshot())
    loader = request.app.state.loader
    model_loaded = True
    model_version = "unknown"
    try:
        bundle = loader.load()
        model_version = bundle.version
    except Exception:
        model_loaded = False

    user_id = int(user["user_id"]) if "user_id" in user else None
    pred_repo = PredictionRepository(db, user_id=user_id)
    total = pred_repo.count_total()
    fraud = pred_repo.count_fraud()
    risk_dist = pred_repo.count_by_risk_level()

    return {
        "prediction_volume": total,
        "fraud_prediction_rate": round(fraud / total, 4) if total > 0 else 0.0,
        "risk_distribution": {
            "low": risk_dist.get("LOW", 0),
            "medium": risk_dist.get("MEDIUM", 0),
            "high": risk_dist.get("HIGH", 0),
        },
        "model_version": model_version,
        "model_loaded": model_loaded,
        "avg_latency_ms": metrics_snapshot.get("average_latency_ms", 0.0),
        "error_count": metrics_snapshot.get("error_count", 0),
        "request_count": total,
        "uptime_seconds": round(time.time() - _START_TIME, 2),
    }


@router.get("/monitoring/drift")
async def monitoring_drift(
    request: Request,
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Latest drift analysis results."""
    drift_dir = request.app.state.settings.production.drift_output_directory
    results = {}
    for name in ("data_drift", "prediction_drift", "model_drift"):
        path = drift_dir / f"{name}.json"
        if path.exists():
            results[name] = json.loads(path.read_text(encoding="utf-8"))
    return {"drift_reports": results, "reports_available": len(results)}


@router.get("/monitoring/model-metrics")
async def monitoring_model_metrics(
    request: Request,
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Current champion model evaluation metrics."""
    loader = request.app.state.loader
    try:
        bundle = loader.load()
        model_version = bundle.version
        model_algorithm = bundle.metadata.get("selected_model", "unknown")
    except Exception:
        model_version = "None loaded"
        model_algorithm = "N/A"
        bundle = None

    metrics = {}
    if bundle and hasattr(bundle, "metadata"):
        comparisons = bundle.metadata.get("comparisons", [])
        for comp in comparisons:
            if comp.get("model_name") == model_algorithm and comp.get("test_metrics"):
                metrics = comp["test_metrics"]
                break

    # Load threshold report if available
    threshold_path = request.app.state.settings.evaluation.output_directory / "threshold_report.csv"
    threshold_data: list[dict[str, float]] = []
    if threshold_path.exists():
        import csv

        with threshold_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                threshold_data.append({k: float(v) for k, v in row.items()})

    return {
        "metrics": metrics,
        "model_version": model_version,
        "model_algorithm": model_algorithm,
        "threshold_analysis": threshold_data[:20],  # First 20 for chart
        "available": True,
    }


@router.get("/batch-jobs")
async def list_batch_jobs(
    user: Annotated[dict[str, str], Depends(current_user)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List recent batch prediction jobs."""
    user_id = int(user["user_id"]) if "user_id" in user else None
    repo = BatchJobRepository(db, user_id=user_id)
    jobs = repo.list_recent(limit=50)
    return {
            "jobs": [
                {
                    "batch_id": j.batch_id,
                    "status": j.status,
                    "total_rows": j.total_rows,
                    "fraud_count": j.fraud_count,
                    "high_risk_count": j.high_risk_count,
                    "medium_risk_count": j.medium_risk_count,
                    "low_risk_count": j.low_risk_count,
                    "model_version": j.model_version,
                    "execution_time_ms": j.execution_time_ms,
                    "created_at": j.created_at.isoformat() if j.created_at else "",
                }
                for j in jobs
            ]
        }
