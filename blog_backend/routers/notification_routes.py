from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Notification, User
from security import get_current_user
from models import User, Post, Like, Comment, Notification

router = APIRouter(prefix="/notifications", tags=["In-App Notifications"])

@router.get("/")
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch notifications for the authenticated user, latest first."""
    notifications = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    unread_count = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id, Notification.is_read == False)
        .count()
    )
    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "message": n.message,
                "type": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at.strftime("%b %d, %H:%M") if n.created_at else ""
            }
            for n in notifications
        ]
    }

@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a single notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    
    notif.is_read = True
    db.commit()
    return {"status": "success", "message": "Marked as read"}

@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all unread notifications as read for the authenticated user."""
    db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success", "message": "All marked as read"}