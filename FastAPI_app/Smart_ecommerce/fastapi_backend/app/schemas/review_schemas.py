from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProductReviewSummary(BaseModel):
    product_id: int
    average_rating: float
    total_reviews: int
    reviews: list[ReviewResponse]