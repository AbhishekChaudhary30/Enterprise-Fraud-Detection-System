"""Health and service metadata endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Return service health and latest model availability."""
    loader = request.app.state.loader
    latest = loader.latest_version()
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "latest_model_version": latest,
    }
