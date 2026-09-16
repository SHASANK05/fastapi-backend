from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

try:
    from core.database import get_db
    from core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from app.core.database import get_db
    from app.core.security import get_current_user

from app.models.ecommerce_models import Product, User

router = APIRouter(prefix="/inventory", tags=["Inventory Management"])


# --- Schemas ---
class StockUpdatePayload(BaseModel):
    product_id: int
    quantity_to_add: int


class LowStockProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category: Optional[str] = None

    class Config:
        from_attributes = True


# --- Endpoints ---
@router.get("/low-stock", response_model=List[LowStockProductResponse])
def get_low_stock_products(
    threshold: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin-only: Retrieve products with stock at or below the given threshold."""
    if getattr(current_user, "role", "").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to view inventory alerts",
        )

    return db.query(Product).filter(Product.stock <= threshold).all()


@router.post("/restock", status_code=status.HTTP_200_OK)
def restock_product(
    payload: StockUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin-only: Add quantity to existing product stock."""
    if getattr(current_user, "role", "").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to restock inventory",
        )

    if payload.quantity_to_add <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity to add must be greater than zero",
        )

    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.stock = (product.stock or 0) + payload.quantity_to_add
    db.commit()
    db.refresh(product)

    return {
        "message": f"Successfully restocked {product.name}",
        "product_id": product.id,
        "new_stock": product.stock,
    }