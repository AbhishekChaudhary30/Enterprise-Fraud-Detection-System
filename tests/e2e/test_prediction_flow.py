"""End-to-end API flow over the public compatibility and versioned contracts."""

import pytest

pytestmark = pytest.mark.e2e


def test_public_prediction_flow(api_client) -> None:
    """A client can authenticate, discover a model, and score synthetic data."""
    login = api_client.post("/login", data={"username": "admin", "password": "test-password"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    models = api_client.get("/models/latest", headers=headers)
    assert models.status_code == 200
    prediction = api_client.post(
        "/predict",
        headers=headers,
        json={"features": {"Amount": 95.0, "V1": 1.4}, "threshold": 0.5},
    )
    assert prediction.status_code == 200
    body = prediction.json()
    assert body["model_version"] == "v2"
    assert body["prediction_id"]
