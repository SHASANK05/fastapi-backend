from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.models.models import AuditLog, User
from app.api.deps import require_role

router = APIRouter(prefix="/audit-logs", tags=["Module 7: Operational Audit Logs"])

class AuditLogOut(BaseModel):
    id: int
    performed_by: str
    action: str
    entity_type: str
    entity_id: Optional[str]
    details: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AuditLogOut])
def get_audit_trail(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
