from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time, datetime
from app.models.models import RoleEnum, LeaveTypeEnum, LeaveStatusEnum, RiskCategoryEnum

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.EMPLOYEE

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    email: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
