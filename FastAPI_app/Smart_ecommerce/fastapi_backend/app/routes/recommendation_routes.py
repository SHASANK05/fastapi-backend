from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Any
from pydantic import BaseModel

try:
    from core.database import get_db
    from core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from app.core.database import get_db
    from app.core.security import get_current_user

from app.models.ecommerce_models import Product, Order, OrderItem


class ProductRecommendationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    stock: Optional[int] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True


router = APIRouter(tags=["Recommendations"])


def _apply_trending_order(query: Any):
    """Sort by view_count if present in model, otherwise sort by latest id."""
    if hasattr(Product, "view_count"):
        return query.order_by(desc(Product.view_count))
    if hasattr(Product, "created_at"):
        return query.order_by(desc(Product.created_at))
    return query.order_by(desc(Product.id))


@router.get("/recommendations/trending", response_model=List[ProductRecommendationResponse])
def get_trending_products(limit: int = 10, db: Session = Depends(get_db)):
    """Fetch top products (trending/popular or latest)."""
    return _apply_trending_order(db.query(Product)).limit(limit).all()


@router.get("/products/{product_id}/similar", response_model=List[ProductRecommendationResponse])
def get_similar_products(product_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """Fetch products in the same category, excluding the current item."""
    target = db.query(Product).filter(Product.id == product_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Product not found")

    query = db.query(Product).filter(
        Product.category == target.category,
        Product.id != product_id,
    )
    return _apply_trending_order(query).limit(limit).all()


@router.get("/recommendations/{user_id}", response_model=List[ProductRecommendationResponse])
def get_user_recommendations(user_id: int, limit: int = 6, db: Session = Depends(get_db)):
    """
    Recommend products from categories previously purchased by the user.
    Falls back to trending/popular items if no purchase history exists.
    """
    # 1. Fetch categories from user's completed/delivered orders
    categories = (
        db.query(Product.category)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            Order.order_status.in_(["Delivered", "Completed", "delivered", "completed"]),
        )
        .distinct()
        .all()
    )
    category_list = [c[0] for c in categories if c[0]]

    # 2. Return unpurchased products from those categories
    if category_list:
        purchased_ids = (
            db.query(OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.user_id == user_id)
            .subquery()
        )

        query = db.query(Product).filter(
            Product.category.in_(category_list),
            Product.id.notin_(purchased_ids),
        )
        recommendations = _apply_trending_order(query).limit(limit).all()
        if recommendations:
            return recommendations

    # 3. Fallback: Trending / Latest products
    return _apply_trending_order(db.query(Product)).limit(limit).all()