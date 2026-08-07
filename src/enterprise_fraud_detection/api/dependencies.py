"""Shared FastAPI dependencies for authentication and service access."""

from __future__ import annotations

from typing import Annotated, Any, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


def current_user(request: Request, token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, str]:
    """Resolve the authenticated user from the request bearer token."""
    return cast(dict[str, str], request.app.state.auth.current_user(token))


def admin_user(user: Annotated[dict[str, str], Depends(current_user)]) -> dict[str, str]:
    """Require the admin role for administrative routes."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


def service(request: Request) -> Any:
    """Resolve the prediction service from application state."""
    return request.app.state.predictions
