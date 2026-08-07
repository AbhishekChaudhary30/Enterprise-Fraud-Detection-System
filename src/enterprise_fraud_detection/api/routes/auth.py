"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from enterprise_fraud_detection.api.schemas import LoginResponse

router = APIRouter()
LOGIN_FORM = Depends()


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, form: OAuth2PasswordRequestForm = LOGIN_FORM) -> LoginResponse:
    """Authenticate the configured admin and return a JWT bearer token."""
    auth = request.app.state.auth
    user = auth.authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return LoginResponse(access_token=auth.create_access_token(user), role=user["role"])
