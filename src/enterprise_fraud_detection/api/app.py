"""FastAPI application factory for the fraud detection service."""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from enterprise_fraud_detection.api.routes import auth, predictions, reports, system
from enterprise_fraud_detection.auth.security import AuthService
from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.serving.model_loader import ModelLoader
from enterprise_fraud_detection.serving.prediction import PredictionService
from enterprise_fraud_detection.utils.logging import configure_logging


def create_app() -> FastAPI:
    """Create a configured FastAPI application with dependency-injected services."""
    settings = get_settings()
    configure_logging(settings)
    app = FastAPI(
        title="Enterprise Fraud Detection API",
        version="1.0.0",
        description="Authenticated fraud scoring and model artifact access service.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.state.settings = settings
    app.state.auth = AuthService(settings)
    app.state.loader = ModelLoader(settings)
    app.state.predictions = PredictionService(settings, app.state.loader)

    @app.middleware("http")
    async def request_logging(request: Request, call_next: Any) -> Any:
        started = time.perf_counter()
        try:
            response = await call_next(request)
            logger.info(
                "API request {} {} completed with {} in {:.2f}ms",
                request.method,
                request.url.path,
                response.status_code,
                (time.perf_counter() - started) * 1000,
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

    prefix = settings.serving.api_prefix
    app.include_router(system.router, prefix=prefix, tags=["system"])
    app.include_router(auth.router, prefix=prefix, tags=["authentication"])
    app.include_router(predictions.router, prefix=prefix, tags=["predictions"])
    app.include_router(reports.router, prefix=prefix, tags=["artifacts"])
    return app


app = create_app()
