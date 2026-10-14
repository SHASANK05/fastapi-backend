from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import User, AuditLog, RoleEnum
from app.dependencies import require_roles

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    target_table: Optional[str]
    target_id: Optional[int]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN))
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()