"""Health, readiness, and service metadata endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Return service health and latest model availability."""
    loader = request.app.state.loader
    try:
        latest = loader.latest_version()
        model_available = True
    except FileNotFoundError:
        latest = None
        model_available = False
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "latest_model_version": latest,
        "model_available": model_available,
    }


@router.get("/ready")
async def ready(request: Request) -> dict[str, Any]:
    """Check if the service is ready to serve predictions."""
    checks: dict[str, bool] = {}

    # Check model availability
    try:
        loader = request.app.state.loader
        loader.latest_version()
        checks["model_loaded"] = True
    except Exception:
        checks["model_loaded"] = False

    # Check database
    try:
        from enterprise_fraud_detection.database.connection import get_db

        with get_db() as db:
            db.execute(db.bind.dialect.do_ping(db.connection()) if hasattr(db, "bind") else None)  # type: ignore[union-attr]
            checks["database"] = True
    except Exception:
        try:
            from sqlalchemy import text

            from enterprise_fraud_detection.database.connection import engine

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["database"] = True
        except Exception:
            checks["database"] = False

    all_ready = all(checks.values())
    return {
        "ready": all_ready,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }
