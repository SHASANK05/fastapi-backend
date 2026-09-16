import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class CommentCreate(BaseModel):
    text: str

class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    text: str
    created_at: datetime.datetime
    user: UserOut

    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    title: str
    content: str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime.datetime
    author: UserOut
    likes_count: int = 0
    comments: List[CommentOut] = []

    class Config:
        from_attributes = True