from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from core.database import get_db
try:
    from core.security import get_current_user
except ModuleNotFoundError:
    from core.security import get_current_user
from app.models.ecommerce_models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatusEnum,
    Payment,
    PaymentStatusEnum,
    Product,
    User,
)

router = APIRouter(prefix="/checkout", tags=["Checkout"])


class CheckoutRequest(BaseModel):
    shipping_address: str
    payment_method: str = "stripe"


class CheckoutResponse(BaseModel):
    order_id: int
    total: float
    order_status: str
    message: str


@router.post("/", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert cart items into a confirmed order and clear the cart."""
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty. Add items before checking out.",
        )

    # Calculate total and check stock
    total_val = 0.0
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item.product_id} no longer exists.",
            )
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for '{product.name}'. Available: {product.stock}",
            )
        total_val += float(product.price) * item.quantity

    # Create Order using exact columns from ecommerce_models.py
    order = Order(
        user_id=current_user.id,
        total=total_val,
        tax_amount=0.0,
        payment_status=PaymentStatusEnum.PAID,
        order_status=OrderStatusEnum.DELIVERED,
    )
    db.add(order)
    db.flush()

    # Create Order Items and decrease stock
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock -= item.quantity
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price=product.price,
            item_total=float(product.price) * item.quantity,
        )
        db.add(order_item)

    # Empty the user's cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()

    return CheckoutResponse(
        order_id=order.id,
        total=order.total,
        order_status=order.order_status.value,
        message="Order placed successfully!",
    )