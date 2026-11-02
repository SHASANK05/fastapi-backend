from pydantic import BaseModel, EmailStr
from app.models import RoleEnum

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.CUSTOMER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str

class UserProfile(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True
