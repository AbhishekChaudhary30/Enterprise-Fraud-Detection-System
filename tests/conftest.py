"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from enterprise_fraud_detection.api.app import app


@pytest.fixture
def api_client() -> TestClient:
    """Return an in-process client for the configured FastAPI application."""
    return TestClient(app)
