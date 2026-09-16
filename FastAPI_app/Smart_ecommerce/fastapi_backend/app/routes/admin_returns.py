from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from app.models.ecommerce_models import (
    ReturnRequest,
    Order,
    User,
    RoleEnum,
    OrderStatusEnum,
    NotificationTypeEnum,
)
try:
    from core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from app.core.security import get_current_user

from app.services.admin_return_service import (
    restock_inventory,
    process_refund,
    create_notification,
)

router = APIRouter(prefix="/admin/returns", tags=["Admin Returns"])


def require_admin(current_user: User = Depends(get_current_user)):
    user_role = str(getattr(current_user.role, "value", current_user.role)).lower()
    if user_role not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


class RejectionPayload(BaseModel):
    reason: Optional[str] = "Item does not meet return policy criteria."


def _normalize_status(val) -> str:
    """Helper to cleanly extract string value from Enum or raw string."""
    if hasattr(val, "value"):
        return str(val.value).strip().lower()
    return str(val).strip().lower() if val is not None else ""


# 1. GET /admin/returns
@router.get("")
def get_all_returns(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    returns = db.query(ReturnRequest).order_by(ReturnRequest.created_at.desc()).all()
    return returns


# 2. POST /admin/returns/{id}/approve
@router.post("/{return_id}/approve")
def approve_return(
    return_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ret = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Return request not found")

    current_status = _normalize_status(ret.status)
    if current_status == "approved":
        raise HTTPException(status_code=400, detail="Request already approved")

    if current_status not in ["pending", ""]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve return with status '{current_status}'",
        )

    order = db.query(Order).filter(Order.id == ret.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Status updates
    ret.status = "approved"
    order.order_status = OrderStatusEnum.RETURNED

    # Restock Inventory
    restock_inventory(db, order)

    # Stripe Refund & Payment Status
    refund_res = process_refund(db, order)

    # Notifications
    create_notification(
        db,
        user_id=ret.user_id,
        notif_type=NotificationTypeEnum.RETURN_APPROVED,
        message=f"Your return request for Order #{order.id} has been approved.",
    )

    if isinstance(refund_res, dict) and refund_res.get("success"):
        create_notification(
            db,
            user_id=ret.user_id,
            notif_type=NotificationTypeEnum.REFUND_COMPLETED,
            message=f"Refund for Order #{order.id} has been completed successfully.",
        )

    db.commit()
    db.refresh(ret)
    db.refresh(order)

    return {
        "message": "Return approved, inventory restored, and refund processed.",
        "return_status": ret.status,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "refund_details": refund_res,
    }


# 3. POST /admin/returns/{id}/reject
@router.post("/{return_id}/reject")
def reject_return(
    return_id: int,
    payload: Optional[RejectionPayload] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ret = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not ret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Return request not found",
        )

    current_status = _normalize_status(ret.status)
    if current_status not in ["pending", ""]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request already {current_status}",
        )

    reason_text = (
        payload.reason
        if payload and payload.reason
        else "Item does not meet return policy criteria."
    )

    ret.status = "rejected"
    db.add(ret)

    create_notification(
        db,
        user_id=ret.user_id,
        notif_type=NotificationTypeEnum.RETURN_REJECTED,
        message=f"Your return for Order #{ret.order_id} was rejected. Reason: {reason_text}",
    )

    db.commit()
    db.refresh(ret)

    return {
        "message": "Return request rejected.",
        "return_status": ret.status,
        "reason": reason_text,
    }