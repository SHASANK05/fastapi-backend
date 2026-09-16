from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Database import
try:
    from app.core.database import get_db
except (ImportError, ModuleNotFoundError):
    from core.database import get_db

# Security import
try:
    from core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from core.security import get_current_user

# Models import
try:
    from app.models.ecommerce_models import (
        Order,
        OrderItem,
        Product,
        ReturnRequest,
        OrderStatusEnum,
        User,
        Notification,
    )
except (ImportError, ModuleNotFoundError):
    from models.ecommerce_models import (
        Order,
        OrderItem,
        Product,
        ReturnRequest,
        OrderStatusEnum,
        User,
        Notification,
    )

router = APIRouter(prefix="/orders", tags=["Orders & Returns"])

class ReturnRequestCreate(BaseModel):
    reason: str
    comment: Optional[str] = None

class ReturnActionPayload(BaseModel):
    admin_notes: Optional[str] = None


@router.post("/{order_id}/return")
def create_return_request(
    order_id: int,
    payload: ReturnRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Fetch Order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} not found.",
        )

    # 2. Ownership Check (Allow admin override for testing)
    user_role = str(getattr(current_user.role, "value", current_user.role)).lower()
    if order.user_id != current_user.id and user_role not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to return this order.",
        )

    # 3. Status Check: Must be 'delivered'
    order_status_val = str(getattr(order.order_status, "value", order.order_status)).lower()
    if order_status_val != "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Returns are only allowed for delivered orders. Current status: {order_status_val}",
        )

    # 4. 7-Day Window Check
    return_window_days = 7
    if order.created_at and (datetime.utcnow() - order.created_at > timedelta(days=return_window_days)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Return window expired. Returns must be requested within {return_window_days} days.",
        )

    # 5. Check if an active/existing request exists
    existing_request = (
        db.query(ReturnRequest).filter(ReturnRequest.order_id == order_id).first()
    )
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A return request already exists for this order with status: {existing_request.status}",
        )

    # 6. Create Return Request Record
    new_return = ReturnRequest(
        order_id=order.id,
        user_id=order.user_id,
        reason=payload.reason,
        comment=payload.comment,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(new_return)

    # 7. Create Confirmation Notification for the user
    notification = Notification(
        user_id=order.user_id,
        notification_type="Return Requested",
        message=f"Return request initiated for Order #{order.id}.",
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(notification)

    db.commit()
    db.refresh(new_return)

    return {
        "message": "Return request submitted successfully.",
        "return_id": new_return.id,
        "order_id": new_return.order_id,
        "status": new_return.status,
    }


# Admin Approval Route
@router.post("/returns/{return_id}/approve")
def approve_return(
    return_id: int,
    payload: Optional[ReturnActionPayload] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_role = str(getattr(current_user.role, "value", current_user.role)).lower()
    if user_role not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to approve returns.",
        )

    return_req = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found.")

    if return_req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Return is already {return_req.status}.")

    return_req.status = "approved"

    # Restore inventory for returned items
    order_items = db.query(OrderItem).filter(OrderItem.order_id == return_req.order_id).all()
    for item in order_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity

    # Create Approval Notification
    notification = Notification(
        user_id=return_req.user_id,
        notification_type="Return Approved",
        message=f"Your return request for Order #{return_req.order_id} has been approved.",
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(notification)

    db.commit()
    return {"message": "Return approved successfully", "return_id": return_id}


# Admin Rejection Route
@router.post("/returns/{return_id}/reject")
def reject_return(
    return_id: int,
    payload: Optional[ReturnActionPayload] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_role = str(getattr(current_user.role, "value", current_user.role)).lower()
    if user_role not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to reject returns.",
        )

    return_req = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found.")

    if return_req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Return is already {return_req.status}.")

    return_req.status = "rejected"

    notes = f" Reason: {payload.admin_notes}" if payload and payload.admin_notes else ""

    # Create Rejection Notification
    notification = Notification(
        user_id=return_req.user_id,
        notification_type="Return Rejected",
        message=f"Your return request for Order #{return_req.order_id} was declined.{notes}",
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(notification)

    db.commit()
    return {"message": "Return rejected", "return_id": return_id}