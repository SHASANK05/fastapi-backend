import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Guarantee 'app' and 'fastapi_backend' are always in sys.path
_current_file = Path(__file__).resolve()
_routes_dir = _current_file.parent
_app_dir = _routes_dir.parent
_backend_dir = _app_dir.parent

for _p in [str(_app_dir), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

# Safe database dependency import
try:
    from app.core.database import get_db
except (ImportError, ModuleNotFoundError):
    from core.database import get_db

# Safe models import
try:
    from app.models.ecommerce_models import User, RoleEnum
except (ImportError, ModuleNotFoundError):
    try:
        from models.ecommerce_models import User, RoleEnum
    except (ImportError, ModuleNotFoundError):
        from ecommerce_models import User, RoleEnum

# Safe security import
try:
    from app.core.security import (
        verify_password,
        get_password_hash,
        create_access_token,
        create_refresh_token,
        get_current_user,
        SECRET_KEY,
        ALGORITHM,
    )
except (ImportError, ModuleNotFoundError):
    try:
        from core.security import (
            verify_password,
            get_password_hash,
            create_access_token,
            create_refresh_token,
            get_current_user,
            SECRET_KEY,
            ALGORITHM,
        )
    except (ImportError, ModuleNotFoundError):
        from security import (
            verify_password,
            get_password_hash,
            create_access_token,
            create_refresh_token,
            get_current_user,
            SECRET_KEY,
            ALGORITHM,
        )

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Schemas ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "customer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# --- Endpoints ---
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    role_choice = RoleEnum.CUSTOMER
    if payload.role and payload.role.lower() == "admin":
        role_choice = RoleEnum.ADMIN
    elif payload.role and payload.role.lower() == "staff":
        role_choice = RoleEnum.STAFF

    new_user = User(
        name=payload.name,
        email=payload.email,
        password=get_password_hash(payload.password),
        role=role_choice,
        created_at=datetime.utcnow(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": str(getattr(new_user.role, "value", new_user.role)),
        },
    }


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {"sub": str(user.id)}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = int(decoded.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "token_type": "bearer",
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": str(getattr(current_user.role, "value", current_user.role)),
        "created_at": current_user.created_at,
    }