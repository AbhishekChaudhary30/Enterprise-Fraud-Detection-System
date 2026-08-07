"""API integration tests using synthetic rows and real temporary pipelines."""

import io

import pandas as pd
import pytest

pytestmark = pytest.mark.integration


def _headers(api_client) -> dict[str, str]:
    """Authenticate against the test app and return bearer headers."""
    response = api_client.post(
        "/api/v1/login", data={"username": "admin", "password": "test-password"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_prediction_batch_upload_and_history(api_client) -> None:
    """Exercise single prediction, batch prediction, CSV upload, and history together."""
    headers = _headers(api_client)
    row = {"Amount": 20.0, "V1": -0.2}
    single = api_client.post("/api/v1/predict", json={"features": row}, headers=headers)
    assert single.status_code == 200
    batch = api_client.post("/api/v1/predict/batch", json={"records": [row]}, headers=headers)
    assert batch.status_code == 200
    csv = pd.DataFrame([row]).to_csv(index=False)
    upload = api_client.post(
        "/api/v1/upload",
        files={"file": ("sample.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=headers,
    )
    assert upload.status_code == 200
    history = api_client.get("/api/v1/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["history"]


def test_metrics_and_security_headers(api_client) -> None:
    """Operational metrics and security headers are exposed by the app."""
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    metrics = api_client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["model_version"] == "v2"
