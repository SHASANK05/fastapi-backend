import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Ensure both 'app' and 'fastapi_backend' directories are present in sys.path
_current_dir = Path(__file__).resolve().parent
_app_dir = _current_dir.parent
_backend_dir = _app_dir.parent

for _p in [str(_backend_dir), str(_app_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
except (ImportError, ModuleNotFoundError):
    from core.database import get_db

try:
    from app.core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from core.security import get_current_user

try:
    from app.models.ecommerce_models import User, Notification
except (ImportError, ModuleNotFoundError):
    try:
        from models.ecommerce_models import User, Notification
    except (ImportError, ModuleNotFoundError):
        from ecommerce_models import User, Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# --- Schemas ---
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    notification_type: Optional[str] = None
    message: str
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    unread_count: int


# --- Helper Functions for Model Attribute Compatibility ---
def _get_read_col():
    if hasattr(Notification, "read_status"):
        return Notification.read_status
    if hasattr(Notification, "is_read"):
        return Notification.is_read
    return None


def _get_order_col():
    if hasattr(Notification, "timestamp"):
        return Notification.timestamp
    if hasattr(Notification, "created_at"):
        return Notification.created_at
    return Notification.id


# --- Endpoints ---

# 1. GET /notifications - List customer's notifications (newest first)
@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    read_col = _get_read_col()

    if unread_only and read_col is not None:
        query = query.filter(read_col == False)

    order_col = _get_order_col()
    notifications = query.order_by(order_col.desc()).all()

    results = []
    for n in notifications:
        n_type = getattr(n, "type", None) or getattr(n, "notification_type", None)
        if hasattr(n_type, "value"):
            n_type = n_type.value

        is_read_val = getattr(n, "read_status", None)
        if is_read_val is None:
            is_read_val = getattr(n, "is_read", False)

        timestamp_val = getattr(n, "timestamp", None) or getattr(n, "created_at", None)

        results.append(
            NotificationResponse(
                id=n.id,
                user_id=n.user_id,
                notification_type=str(n_type) if n_type else None,
                message=n.message,
                is_read=bool(is_read_val),
                created_at=timestamp_val,
            )
        )
    return results


# 2. GET /notifications/unread-count - Fast counter for notification badge
@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    read_col = _get_read_col()
    if read_col is None:
        return {"unread_count": 0}

    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            read_col == False,
        )
        .count()
    )
    return {"unread_count": count}


# 3. PATCH /notifications/read-all - Mark all unread notifications as read
@router.patch("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    read_col = _get_read_col()
    if read_col is None:
        return {"message": "No read status column found on model.", "marked_count": 0}

    # Select the exact column name present on the SQLAlchemy model
    update_field = "read_status" if hasattr(Notification, "read_status") else "is_read"

    updated_count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            read_col == False,
        )
        .update({update_field: True}, synchronize_session=False)
    )
    db.commit()
    return {
        "message": f"All {updated_count} unread notifications marked as read.",
        "marked_count": updated_count,
    }


# 4. PATCH /notifications/{notification_id}/read - Mark single notification as read
@router.patch("/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )

    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    current_read = getattr(notif, "read_status", None)
    if current_read is None:
        current_read = getattr(notif, "is_read", False)

    if not current_read:
        if hasattr(notif, "read_status"):
            notif.read_status = True
        elif hasattr(notif, "is_read"):
            notif.is_read = True
        db.commit()
        db.refresh(notif)

    final_read = getattr(notif, "read_status", None)
    if final_read is None:
        final_read = getattr(notif, "is_read", True)

    return {
        "message": f"Notification #{notif.id} marked as read.",
        "notification_id": notif.id,
        "is_read": bool(final_read),
    }