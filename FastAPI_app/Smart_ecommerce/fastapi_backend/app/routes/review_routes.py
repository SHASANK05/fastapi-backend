from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

try:
    from core.database import get_db
    from core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from app.core.database import get_db
    from app.core.security import get_current_user

from app.models.ecommerce_models import User, Product, Order, OrderItem, Review
from app.schemas.review_schemas import ReviewCreate, ReviewResponse, ProductReviewSummary

router = APIRouter(tags=["Reviews & Ratings"])


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def submit_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Verify product exists
    product = db.query(Product).filter(Product.id == review_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 2. Prevent duplicate reviews
    existing_review = (
        db.query(Review)
        .filter(
            Review.user_id == current_user.id,
            Review.product_id == review_data.product_id,
        )
        .first()
    )
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")

    # 3. Restrict reviews to delivered/completed purchases using Order.order_status
    verified_purchase = (
        db.query(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == review_data.product_id,
            Order.order_status.in_(["Delivered", "Completed", "delivered", "completed"]),
        )
        .first()
    )
    if not verified_purchase:
        raise HTTPException(
            status_code=403,
            detail="Only users who purchased and received this product can review it",
        )

    # 4. Create and save review
    new_review = Review(
        user_id=current_user.id,
        product_id=review_data.product_id,
        rating=review_data.rating,
        comment=review_data.comment,
        status="approved",
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


@router.get("/products/{product_id}/reviews", response_model=ProductReviewSummary)
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.status == "approved")
        .all()
    )

    total_reviews = len(reviews)
    avg_rating = (
        round(sum(r.rating for r in reviews) / total_reviews, 2)
        if total_reviews > 0
        else 0.0
    )

    return ProductReviewSummary(
        product_id=product_id,
        average_rating=avg_rating,
        total_reviews=total_reviews,
        reviews=reviews,
    )