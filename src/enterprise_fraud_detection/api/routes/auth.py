"""Authentication endpoints."""

from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from enterprise_fraud_detection.api.schemas import LoginResponse, RegisterRequest
from enterprise_fraud_detection.database.connection import get_db
from enterprise_fraud_detection.database.models import User

router = APIRouter()
LOGIN_FORM = Depends()

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, form: OAuth2PasswordRequestForm = LOGIN_FORM, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate the user and return a JWT bearer token."""
    auth = request.app.state.auth
    
    # Check DB first
    user = db.query(User).filter(User.username == form.username).first()
    if user and auth.password_context.verify(form.password, user.password_hash):
        subject = {"username": user.username, "role": user.role, "user_id": str(user.id)}
        return LoginResponse(access_token=auth.create_access_token(subject), role=user.role)
        
    # Fallback to configured admin
    fallback_user = auth.authenticate(form.username, form.password)
    if fallback_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return LoginResponse(access_token=auth.create_access_token(fallback_user), role=fallback_user["role"])

@router.post("/register", response_model=LoginResponse)
async def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Register a new user."""
    auth = request.app.state.auth
    
    # Check if username exists
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
    # Create user
    hashed_pw = auth.password_context.hash(payload.password)
    user = User(username=payload.username, password_hash=hashed_pw, role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    subject = {"username": user.username, "role": user.role, "user_id": str(user.id)}
    return LoginResponse(access_token=auth.create_access_token(subject), role=user.role)

@router.post("/guest", response_model=LoginResponse)
async def guest_login(request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    """Create a temporary guest account and login automatically."""
    auth = request.app.state.auth
    
    guest_username = f"guest_{uuid.uuid4().hex[:8]}"
    hashed_pw = auth.password_context.hash(uuid.uuid4().hex)
    user = User(username=guest_username, password_hash=hashed_pw, role="guest")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    subject = {"username": user.username, "role": user.role, "user_id": str(user.id)}
    return LoginResponse(access_token=auth.create_access_token(subject), role=user.role)
