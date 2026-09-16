import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Ensure both 'app' and 'fastapi_backend' are in sys.path
_current_file = Path(__file__).resolve()
_routes_dir = _current_file.parent
_app_dir = _routes_dir.parent
_backend_dir = _app_dir.parent

for _p in [str(_backend_dir), str(_app_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Safe database dependency import
try:
    from app.core.database import get_db
except (ImportError, ModuleNotFoundError):
    from core.database import get_db

# Safe security import
try:
    from app.core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from core.security import get_current_user

# Safe models import with full 3-tier fallback
try:
    from app.models.ecommerce_models import (
        User,
        Order,
        OrderItem,
        Product,
        ReturnRequest,
        OrderStatusEnum,
        NotificationTypeEnum,
        Coupon,
        Notification,
    )
except (ImportError, ModuleNotFoundError):
    try:
        from models.ecommerce_models import (
            User,
            Order,
            OrderItem,
            Product,
            ReturnRequest,
            OrderStatusEnum,
            NotificationTypeEnum,
            Coupon,
            Notification,
        )
    except (ImportError, ModuleNotFoundError):
        from ecommerce_models import (
            User,
            Order,
            OrderItem,
            Product,
            ReturnRequest,
            OrderStatusEnum,
            NotificationTypeEnum,
            Coupon,
            Notification,
        )

# Safe notification helper import
try:
    from app.services.admin_return_service import create_notification
except (ImportError, ModuleNotFoundError):
    try:
        from services.admin_return_service import create_notification
    except (ImportError, ModuleNotFoundError):
        def create_notification(db: Session, user_id: int, notif_type, message: str):
            try:
                notif = Notification(
                    user_id=user_id,
                    type=notif_type,
                    message=message,
                    read_status=False,
                    timestamp=datetime.utcnow(),
                )
                db.add(notif)
                db.commit()
            except Exception:
                db.rollback()

router = APIRouter(prefix="/orders", tags=["Orders"])


class ReturnRequestCreate(BaseModel):
    reason: str
    comment: Optional[str] = None


class OrderItemInput(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, description="Quantity must be at least 1")


class CreateOrderPayload(BaseModel):
    items: List[OrderItemInput]
    coupon_code: Optional[str] = None


# 1. POST /orders - Create order with discount calculation and atomic inventory decrement
@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(
    payload: CreateOrderPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item.",
        )

    # 1. Validate all products and stock availability before writing
    validated_products = []
    subtotal = 0.0

    for item_in in payload.items:
        product = (
            db.query(Product)
            .filter(Product.id == item_in.product_id)
            .with_for_update()
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item_in.product_id} not found.",
            )

        if (product.stock or 0) < item_in.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}, requested: {item_in.quantity}",
            )

        line_total = float(product.price) * item_in.quantity
        subtotal += line_total
        validated_products.append((product, item_in.quantity, float(product.price), line_total))

    # 2. Apply optional coupon discount
    discount_amount = 0.0
    applied_coupon_code = None

    if payload.coupon_code:
        c_code = payload.coupon_code.strip().upper()
        coupon = db.query(Coupon).filter(Coupon.code == c_code, Coupon.is_active == True).first()

        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or inactive coupon code.",
            )

        now = datetime.utcnow()
        if coupon.valid_until and coupon.valid_until < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This coupon has expired.",
            )

        min_req = coupon.min_order_amount or 0.0
        if subtotal < min_req:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum order of ₹{min_req} required for coupon '{coupon.code}'.",
            )

        discount_amount = (subtotal * coupon.discount_percent) / 100.0
        if coupon.max_discount_amount and discount_amount > coupon.max_discount_amount:
            discount_amount = coupon.max_discount_amount

        discount_amount = round(discount_amount, 2)
        applied_coupon_code = coupon.code

    discounted_subtotal = round(max(0.0, subtotal - discount_amount), 2)

    # 3. Compute tax and final grand total
    tax_rate = 0.05  # 5% tax
    tax_amount = round(discounted_subtotal * tax_rate, 2)
    grand_total = round(discounted_subtotal + tax_amount, 2)

    # 4. Create the Order header
    status_val = getattr(OrderStatusEnum, "DELIVERED", None) or "delivered"
    if hasattr(status_val, "value"):
        status_val = status_val.value

    new_order = Order(
        user_id=current_user.id,
        total=grand_total,
        tax_amount=tax_amount,
        order_status=status_val,
        payment_status="paid",
        created_at=datetime.utcnow(),
    )
    db.add(new_order)
    db.flush()

    # 5. Decrement inventory stock & create OrderItems
    order_items_out = []
    for product, qty, unit_price, line_total in validated_products:
        product.stock -= qty

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
            item_total=line_total,
        )
        db.add(order_item)
        order_items_out.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": qty,
            "unit_price": unit_price,
            "item_total": line_total,
            "remaining_stock": product.stock,
        })

    # 6. Notification event
    try:
        notif_type = getattr(NotificationTypeEnum, "ORDER_CONFIRMED", None) or getattr(NotificationTypeEnum, "CART_UPDATED", None)
        create_notification(
            db,
            user_id=current_user.id,
            notif_type=notif_type,
            message=f"Order #{new_order.id} confirmed for ₹{grand_total}.",
        )
    except Exception:
        pass

    db.commit()
    db.refresh(new_order)

    return {
        "message": "Order created successfully and inventory decremented.",
        "order_id": new_order.id,
        "subtotal": round(subtotal, 2),
        "coupon_applied": applied_coupon_code,
        "discount_amount": discount_amount,
        "tax_amount": new_order.tax_amount,
        "total": new_order.total,
        "order_status": new_order.order_status,
        "items": order_items_out,
    }


# 2. GET /orders - View customer's order history
@router.get("")
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    results = []
    for ord_obj in orders:
        items = (
            db.query(OrderItem).filter(OrderItem.order_id == ord_obj.id).all()
        )
        item_data = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "item_total": item.item_total,
            }
            for item in items
        ]
        results.append(
            {
                "order_id": ord_obj.id,
                "total": ord_obj.total,
                "tax_amount": ord_obj.tax_amount,
                "order_status": ord_obj.order_status,
                "payment_status": ord_obj.payment_status,
                "created_at": ord_obj.created_at,
                "items": item_data,
            }
        )
    return results


# 3. GET /orders/{order_id} - View specific order details
@router.get("/{order_id}")
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )

    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return {
        "order_id": order.id,
        "total": order.total,
        "tax_amount": order.tax_amount,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "created_at": order.created_at,
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "item_total": item.item_total,
            }
            for item in items
        ],
    }


# 4. POST /orders/{order_id}/return - Customer initiates a return request
@router.post("/{order_id}/return", status_code=status.HTTP_201_CREATED)
def request_order_return(
    order_id: int,
    payload: ReturnRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )

    existing_return = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.order_id == order_id)
        .first()
    )
    if existing_return:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A return request already exists with status: {existing_return.status}",
        )

    new_return = ReturnRequest(
        order_id=order.id,
        user_id=current_user.id,
        reason=payload.reason,
        comment=payload.comment,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(new_return)
    db.commit()
    db.refresh(new_return)

    try:
        notif_type = getattr(NotificationTypeEnum, "CART_UPDATED", None) or "return_requested"
        create_notification(
            db,
            user_id=current_user.id,
            notif_type=notif_type,
            message=f"Return request initiated for Order #{order.id}.",
        )
    except Exception:
        pass

    return {
        "message": "Return request submitted successfully.",
        "return_id": new_return.id,
        "status": new_return.status,
    }


# 5. POST /orders/{order_id}/cancel - Cancel order and restore product stock
@router.post("/{order_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Order).filter(Order.id == order_id)
    role_val = getattr(current_user, "role", "")
    if hasattr(role_val, "value"):
        role_val = role_val.value

    if str(role_val).lower() != "admin":
        query = query.filter(Order.user_id == current_user.id)

    order = query.first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    curr_status = str(order.order_status).lower()
    if "cancel" in curr_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already cancelled.",
        )

    if curr_status in ["returned", "refunded"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an order with status '{order.order_status}'.",
        )

    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    restored_items = []

    for item in order_items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .with_for_update()
            .first()
        )
        if product:
            product.stock = (product.stock or 0) + item.quantity
            restored_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "restored_quantity": item.quantity,
                "current_stock": product.stock,
            })

    cancel_status = getattr(OrderStatusEnum, "CANCELLED", None) or "cancelled"
    if hasattr(cancel_status, "value"):
        cancel_status = cancel_status.value

    order.order_status = cancel_status
    if hasattr(order, "payment_status"):
        order.payment_status = "refunded"

    try:
        notif_type = getattr(NotificationTypeEnum, "ORDER_SHIPPED", None) or getattr(NotificationTypeEnum, "CART_UPDATED", None)
        create_notification(
            db,
            user_id=order.user_id,
            notif_type=notif_type,
            message=f"Order #{order.id} has been cancelled and refunded.",
        )
    except Exception:
        pass

    db.commit()
    db.refresh(order)

    return {
        "message": f"Order #{order.id} cancelled successfully and stock restored.",
        "order_id": order.id,
        "order_status": order.order_status,
        "restored_items": restored_items,
    }