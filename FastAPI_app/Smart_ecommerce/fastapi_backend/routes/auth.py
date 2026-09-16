from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.ecommerce_models import User, RoleEnum

def get_current_user(db: Session = Depends(get_db)) -> User:
    """Ensure mock test user exists in MySQL and return it."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="mockhashedpassword123",
            is_active=True,
            is_admin=True,
            role=getattr(RoleEnum, "ADMIN", "admin")
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            user = db.query(User).first()
    else:
        if hasattr(user, "role") and user.role != getattr(RoleEnum, "ADMIN", "admin"):
            user.role = getattr(RoleEnum, "ADMIN", "admin")
            db.commit()
            db.refresh(user)

    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Validate admin privileges."""
    admin_role = getattr(RoleEnum, "ADMIN", "admin")
    user_role = getattr(current_user, "role", None)
    is_admin = getattr(current_user, "is_admin", False)

    if user_role != admin_role and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user