"""Health, readiness, and service metadata endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from enterprise_fraud_detection.database.connection import get_db

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
        from sqlalchemy import text
        from enterprise_fraud_detection.database.connection import SessionLocal

        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
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


@router.get("/debug")
async def debug(request: Request) -> dict[str, Any]:
    """Debug endpoint to trace where the 500 error happens."""
    results = {}
    import traceback
    
    # Test passlib hashing
    try:
        auth = request.app.state.auth
        pw_hash = auth.password_context.hash("test_password")
        results["passlib"] = "success"
    except Exception as e:
        results["passlib_error"] = traceback.format_exc()
        
        # Test DB User table
    try:
        from enterprise_fraud_detection.database.connection import SessionLocal
        with SessionLocal() as db:
            from enterprise_fraud_detection.database.models import User
            users = db.query(User).limit(1).all()
            results["db_users"] = f"success, count: {len(users)}"
    except Exception as e:
        results["db_error"] = traceback.format_exc()
        
    try:
        from enterprise_fraud_detection.database.connection import engine
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE predictions ADD COLUMN is_archived BOOLEAN DEFAULT FALSE"))
            results["alter_table"] = "success"
    except Exception as e:
        results["alter_table_error"] = traceback.format_exc()

    return results
