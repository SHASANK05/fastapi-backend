from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db          # adjust import path if needed
from ..models.ecommerce_models import Order, ReturnRequest, User
from ..routes.auth_routes import get_current_user  # adjust import to your auth dependency

router = APIRouter(prefix="/orders", tags=["Orders"])

class ReturnCreateSchema(BaseModel):
    reason: str
    comment: Optional[str] = None

RETURN_WINDOW_DAYS = 365

@router.post("/{order_id}/return", status_code=status.HTTP_201_CREATED)
def request_order_return(
    order_id: int,
    payload: ReturnCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch order
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2. Check Order Status
    if order.order_status.lower() != "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Returns only allowed for delivered orders. Current status: {order.order_status}"
        )

    # 3. Check 7-Day Window
    order_time = order.created_at
    if order_time.tzinfo is None:
        order_time = order_time.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) - order_time > timedelta(days=RETURN_WINDOW_DAYS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Return window expired. Must be requested within {RETURN_WINDOW_DAYS} days."
        )

    # 4. Check duplicate requests
    existing = db.query(ReturnRequest).filter(ReturnRequest.order_id == order_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Return request already exists with status: {existing.status}"
        )

    # 5. Create Return Request
    return_req = ReturnRequest(
        order_id=order.id,
        user_id=current_user.id,
        reason=payload.reason,
        comment=payload.comment,
        status="pending"
    )
    db.add(return_req)
    db.commit()
    db.refresh(return_req)

    return {
        "message": "Return request submitted successfully",
        "return_id": return_req.id,
        "status": return_req.status
    }

@router.get("/{order_id}/return")
def get_order_return_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return_req = db.query(ReturnRequest).filter(
        ReturnRequest.order_id == order_id,
        ReturnRequest.user_id == current_user.id
    ).first()

    if not return_req:
        raise HTTPException(status_code=404, detail="No return request found for this order")

    return {
        "order_id": return_req.order_id,
        "status": return_req.status,
        "reason": return_req.reason,
        "comment": return_req.comment,
        "created_at": return_req.created_at
    }