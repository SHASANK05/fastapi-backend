import json
from sqlalchemy.orm import Session
from app.models.models import AuditLog

def log_activity(
    db: Session,
    performed_by: str,
    action: str,
    entity_type: str,
    entity_id: str = None,
    details: dict = None
):
    details_str = json.dumps(details) if details else None
    audit_entry = AuditLog(
        performed_by=performed_by,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details_str
    )
    db.add(audit_entry)
    db.commit()
