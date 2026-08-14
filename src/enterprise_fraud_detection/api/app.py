"""FastAPI application factory for the Enterprise Fraud Intelligence Platform."""

from __future__ import annotations

import time
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from enterprise_fraud_detection.api.routes import (
    auth,
    investigations,
    monitoring,
    predictions,
    reports,
    system,
)
from enterprise_fraud_detection.auth.security import AuthService
from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.database.connection import init_db
from enterprise_fraud_detection.monitoring.metrics import MetricsRegistry
from enterprise_fraud_detection.monitoring.security import RateLimiter, SecurityMiddleware
from enterprise_fraud_detection.serving.model_loader import ModelLoader
from enterprise_fraud_detection.serving.prediction import PredictionService
from enterprise_fraud_detection.utils.logging import configure_logging


def create_app() -> FastAPI:
    """Create a configured FastAPI application with dependency-injected services."""
    settings = get_settings()
    configure_logging(settings)
    app = FastAPI(
        title="Enterprise Fraud Intelligence API",
        version="2.0.0",
        description=(
            "Production-grade fraud detection platform with real ML predictions, "
            "risk scoring, SHAP explanations, investigation workflows, and monitoring."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Initialize services
    app.state.settings = settings
    app.state.auth = AuthService(settings)
    app.state.loader = ModelLoader(settings)
    app.state.predictions = PredictionService(settings, app.state.loader)
    app.state.metrics = MetricsRegistry(settings.production.metrics_path)

    # CORS for React frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security middleware
    app.add_middleware(
        SecurityMiddleware,
        limiter=RateLimiter(
            settings.production.rate_limit_requests,
            settings.production.rate_limit_window_seconds,
        ),
        request_id_header=settings.production.request_id_header,
    )

    @app.middleware("http")
    async def request_logging(request: Request, call_next: Any) -> Any:
        started = time.perf_counter()
        try:
            response = await call_next(request)
            latency_ms = (time.perf_counter() - started) * 1000
            request.app.state.metrics.observe_request(latency_ms, response.status_code)
            logger.info(
                "API {} {} → {} in {:.1f}ms",
                request.method,
                request.url.path,
                response.status_code,
                latency_ms,
            )
            return response
        except Exception:
            logger.exception("API request failed: {} {}", request.method, request.url.path)
            raise

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        del request
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(FileNotFoundError)
    async def not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
        del request
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.get("/metrics", tags=["system"])
    async def metrics() -> dict[str, Any]:
        """Return process and API metrics for operators."""
        snapshot = cast(dict[str, Any], app.state.metrics.snapshot())
        try:
            bundle = app.state.loader.load()
            snapshot["model_version"] = bundle.version
            snapshot["model_name"] = bundle.metadata.get("selected_model")
        except Exception:
            snapshot["model_version"] = "unavailable"
            snapshot["model_name"] = "unavailable"
        return snapshot

    # Register versioned API routes
    prefix = settings.serving.api_prefix
    app.include_router(system.router, prefix=prefix, tags=["system"])
    app.include_router(auth.router, prefix=prefix, tags=["authentication"])
    app.include_router(predictions.router, prefix=prefix, tags=["predictions"])
    app.include_router(reports.router, prefix=prefix, tags=["models & reports"])
    app.include_router(investigations.router, prefix=prefix, tags=["investigations"])
    app.include_router(monitoring.router, prefix=prefix, tags=["monitoring"])

    # Register model versions from disk into database on startup
    _register_model_versions(app)

    logger.info("Enterprise Fraud Intelligence API started")
    return app


def _register_model_versions(app: FastAPI) -> None:
    """Sync disk-based model versions into the database registry."""
    try:
        from enterprise_fraud_detection.database.connection import get_db
        from enterprise_fraud_detection.database.repositories import ModelVersionRepository

        loader = app.state.loader
        versions = loader.versions()
        latest = loader.latest_version() if versions else None

        with get_db() as db:
            repo = ModelVersionRepository(db)
            for version in versions:
                try:
                    existing = db.query(
                        __import__("enterprise_fraud_detection.database.models", fromlist=["ModelVersion"]).ModelVersion
                    ).filter_by(version=version).first()
                    if existing:
                        continue
                    bundle = loader.load(version)
                    metadata = bundle.metadata
                    comparisons = metadata.get("comparisons", [])
                    selected = metadata.get("selected_model", "unknown")
                    # Find test metrics for the selected model
                    test_metrics = {}
                    for comp in comparisons:
                        if comp.get("model_name") == selected and comp.get("test_metrics"):
                            test_metrics = comp["test_metrics"]
                            break
                    status = "champion" if version == latest else "archived"
                    repo.register(
                        version=version,
                        algorithm=selected,
                        metrics=test_metrics or None,
                        row_count=metadata.get("row_count"),
                        training_duration=metadata.get("training_duration_seconds"),
                        status=status,
                    )
                except Exception as exc:
                    logger.warning("Failed to register model {}: {}", version, exc)
            db.commit()
    except Exception as exc:
        logger.warning("Model version registration skipped: {}", exc)


app = create_app()
