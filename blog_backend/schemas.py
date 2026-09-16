from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class CommentCreate(BaseModel):
    text: str

class CommentOut(BaseModel):
    id: int
    text: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str] = None
    author_id: int
    created_at: datetime
    likes_count: int = 0
    comments: List[CommentOut] = []

    class Config:
        from_attributes = True

class PaginatedPostsResponse(BaseModel):
    total_count: int
    total_pages: int
    current_page: int
    limit: int
    posts: List[PostOut]
