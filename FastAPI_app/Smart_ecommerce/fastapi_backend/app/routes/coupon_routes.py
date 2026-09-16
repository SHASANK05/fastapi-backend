from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
except (ImportError, ModuleNotFoundError):
    from core.database import get_db

try:
    from core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from app.core.security import get_current_user

try:
    from app.models.ecommerce_models import User, Coupon
except (ImportError, ModuleNotFoundError):
    from models.ecommerce_models import User, Coupon

router = APIRouter(prefix="/coupons", tags=["Coupons & Discounts"])


# --- Schemas ---
class CouponCreate(BaseModel):
    code: str = Field(..., examples=["FESTIVE20"])
    discount_percent: float = Field(..., gt=0, le=100, examples=[20.0])
    max_discount_amount: Optional[float] = Field(None, examples=[1000.0])
    min_order_amount: Optional[float] = Field(0.0, examples=[2000.0])
    valid_until: Optional[datetime] = None


class CouponApplyRequest(BaseModel):
    code: str = Field(..., examples=["FESTIVE20"])
    cart_total: float = Field(..., gt=0, examples=[6000.0])


class CouponResponse(BaseModel):
    id: int
    code: str
    discount_percent: float
    max_discount_amount: Optional[float]
    min_order_amount: float
    is_active: bool
    valid_until: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Endpoints ---

# 1. POST /coupons/apply - Validate & preview discount calculation
@router.post("/apply", status_code=status.HTTP_200_OK)
def apply_coupon(
    payload: CouponApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    code_clean = payload.code.strip().upper()
    coupon = db.query(Coupon).filter(Coupon.code == code_clean).first()

    if not coupon or not coupon.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or inactive coupon code.",
        )

    now = datetime.utcnow()
    if coupon.valid_until and coupon.valid_until < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This coupon has expired.",
        )

    min_required = coupon.min_order_amount or 0.0
    if payload.cart_total < min_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum cart value of ₹{min_required} required to use this coupon.",
        )

    # Compute discount with optional cap
    discount = (payload.cart_total * coupon.discount_percent) / 100.0
    if coupon.max_discount_amount and discount > coupon.max_discount_amount:
        discount = coupon.max_discount_amount

    discount = round(discount, 2)
    final_total = round(max(0.0, payload.cart_total - discount), 2)

    return {
        "coupon_code": coupon.code,
        "discount_percent": coupon.discount_percent,
        "discount_amount": discount,
        "original_total": payload.cart_total,
        "discounted_total": final_total,
        "message": f"Coupon applied! You saved ₹{discount}.",
    }


# 2. POST /coupons - Admin creates a new coupon
@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    payload: CouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_val = getattr(current_user, "role", "")
    if hasattr(role_val, "value"):
        role_val = role_val.value

    if str(role_val).lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to create coupons.",
        )

    code_clean = payload.code.strip().upper()
    existing = db.query(Coupon).filter(Coupon.code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coupon code '{code_clean}' already exists.",
        )

    coupon = Coupon(
        code=code_clean,
        discount_percent=payload.discount_percent,
        max_discount_amount=payload.max_discount_amount,
        min_order_amount=payload.min_order_amount or 0.0,
        is_active=True,
        valid_until=payload.valid_until,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


# 3. GET /coupons - List all active and unexpired coupons
@router.get("", response_model=List[CouponResponse])
def list_active_coupons(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    coupons = (
        db.query(Coupon)
        .filter(Coupon.is_active == True)
        .all()
    )
    return [c for c in coupons if c.valid_until is None or c.valid_until >= now]


# 4. DELETE /coupons/{coupon_id} - Admin deactivates a coupon
@router.delete("/{coupon_id}", status_code=status.HTTP_200_OK)
def deactivate_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_val = getattr(current_user, "role", "")
    if hasattr(role_val, "value"):
        role_val = role_val.value

    if str(role_val).lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to deactivate coupons.",
        )

    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found.",
        )

    coupon.is_active = False
    db.commit()
    return {"message": f"Coupon '{coupon.code}' has been deactivated successfully."}