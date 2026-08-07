"""API and CSV workflow integration tests."""

import io

import pandas as pd

from enterprise_fraud_detection.config import get_settings


def _token(api_client) -> str:
    settings = get_settings()
    response = api_client.post(
        "/api/v1/login",
        data={
            "username": settings.serving.admin_username,
            "password": settings.serving.admin_password,
        },
    )
    return response.json()["access_token"]


def test_health_and_prediction_workflow(api_client) -> None:
    """Health, single prediction, batch prediction, upload, and history work together."""
    settings = get_settings()
    headers = {"Authorization": f"Bearer {_token(api_client)}"}
    row = (
        pd.read_csv(settings.paths.raw_data / settings.dataset.filename, nrows=1)
        .drop(columns=[settings.dataset.target_column])
        .iloc[0]
        .to_dict()
    )
    assert api_client.get("/api/v1/health").status_code == 200
    assert (
        api_client.post("/api/v1/predict", json={"features": row}, headers=headers).status_code
        == 200
    )
    assert (
        api_client.post(
            "/api/v1/predict/batch", json={"records": [row]}, headers=headers
        ).status_code
        == 200
    )
    csv = pd.DataFrame([row]).to_csv(index=False)
    upload = api_client.post(
        "/api/v1/upload",
        files={"file": ("sample.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=headers,
    )
    assert upload.status_code == 200
    assert api_client.get("/api/v1/history", headers=headers).status_code == 200
