from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.database import get_db
from app.models.models import User, Employee, RoleEnum
from app.core.security import verify_password, create_access_token, get_password_hash
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Module 1: Authentication & RBAC"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str

class UserProfileOut(BaseModel):
    id: int
    email: str
    role: str
    employee_id: Optional[int] = None
    employee_code: Optional[str] = None
    full_name: Optional[str] = None
    designation: Optional[str] = None
    department_name: Optional[str] = None

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect corporate email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    token = create_access_token(data={"sub": user.email, "role": user.role.value})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "email": user.email
    }

@router.get("/me", response_model=UserProfileOut)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    return UserProfileOut(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        employee_id=emp.id if emp else None,
        employee_code=emp.employee_code if emp else None,
        full_name=f"{emp.first_name} {emp.last_name}" if emp else "System Administrator",
        designation=emp.designation if emp else "Executive Admin",
        department_name=emp.department.name if emp and emp.department else "Headquarters"
    )
