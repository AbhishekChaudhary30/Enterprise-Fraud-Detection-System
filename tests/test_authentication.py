"""Authentication behavior tests."""

from enterprise_fraud_detection.config import get_settings


def test_login_and_protected_route(api_client) -> None:
    """Configured credentials issue a token accepted by protected routes."""
    settings = get_settings()
    response = api_client.post(
        "/api/v1/login",
        data={
            "username": settings.serving.admin_username,
            "password": settings.serving.admin_password,
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    protected = api_client.get("/api/v1/models", headers={"Authorization": f"Bearer {token}"})
    assert protected.status_code == 200


def test_protected_route_rejects_anonymous(api_client) -> None:
    """Protected model metadata cannot be accessed without a bearer token."""
    assert api_client.get("/api/v1/models").status_code == 401
