"""JWT token creation and protected FastAPI dependencies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from enterprise_fraud_detection.config.settings import Settings


class AuthService:
    """Authenticate configured admin credentials and issue role-bearing JWTs."""

    def __init__(self, settings: Settings) -> None:
        """Initialize password hashing and token configuration."""
        self.settings = settings
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.serving.api_prefix}/login")

    def authenticate(self, username: str, password: str) -> dict[str, str] | None:
        """Authenticate admin or the configured user credentials."""
        if username != self.settings.serving.admin_username:
            return None
        if password != self.settings.serving.admin_password:
            return None
        return {"username": username, "role": "admin"}

    def create_access_token(self, subject: dict[str, str]) -> str:
        """Create a signed access token containing identity and role."""
        expires = datetime.now(UTC) + timedelta(
            minutes=self.settings.serving.access_token_expire_minutes
        )
        payload = {"sub": subject["username"], "role": subject["role"], "exp": expires}
        return cast(
            str,
            jwt.encode(
                payload,
                self.settings.serving.jwt_secret,
                algorithm=self.settings.serving.jwt_algorithm,
            ),
        )

    def current_user(self, token: str) -> dict[str, str]:
        """Decode and validate a bearer token."""
        credentials_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self.settings.serving.jwt_secret,
                algorithms=[self.settings.serving.jwt_algorithm],
            )
            username = payload.get("sub")
            role = payload.get("role")
            if not isinstance(username, str) or not isinstance(role, str):
                raise credentials_error
            return {"username": username, "role": role}
        except JWTError as error:
            raise credentials_error from error
