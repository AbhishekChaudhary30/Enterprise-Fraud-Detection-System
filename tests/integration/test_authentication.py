"""Authentication integration tests against the actual FastAPI routes."""

import pytest

pytestmark = pytest.mark.integration


def test_login_and_protected_route(api_client) -> None:
    """Configured temporary credentials issue a token accepted by protected routes."""
    response = api_client.post(
        "/api/v1/login", data={"username": "admin", "password": "test-password"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    protected = api_client.get("/api/v1/models", headers={"Authorization": f"Bearer {token}"})
    assert protected.status_code == 200


def test_unversioned_login_compatibility_route(api_client) -> None:
    """The legacy `/login` contract remains available for existing clients."""
    response = api_client.post("/login", data={"username": "admin", "password": "test-password"})
    assert response.status_code == 200


def test_protected_route_rejects_anonymous(api_client) -> None:
    """Protected model metadata rejects missing bearer credentials."""
    assert api_client.get("/api/v1/models").status_code == 401
