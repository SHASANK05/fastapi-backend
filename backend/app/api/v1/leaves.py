from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import date
from app.core.database import get_db
from app.models.models import Leave, LeaveStatusEnum, LeaveTypeEnum, User
from app.api.deps import require_role
from app.services.audit import log_activity

router = APIRouter(prefix="/leaves", tags=["Module 5: Leave Management"])

class LeaveCreate(BaseModel):
    employee_id: int
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: str = None

class LeaveOut(BaseModel):
    id: int
    employee_id: int
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    total_days: int
    status: LeaveStatusEnum
    reason: str = None

    class Config:
        from_attributes = True

@router.post("/", response_model=LeaveOut, status_code=status.HTTP_201_CREATED)
def apply_leave(
    leave_in: LeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "EMPLOYEE"]))
):
    days = (leave_in.end_date - leave_in.start_date).days + 1
    if days <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")

    new_leave = Leave(
        employee_id=leave_in.employee_id,
        leave_type=leave_in.leave_type,
        start_date=leave_in.start_date,
        end_date=leave_in.end_date,
        total_days=days,
        reason=leave_in.reason,
        status=LeaveStatusEnum.PENDING
    )
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return new_leave

@router.get("/", response_model=List[LeaveOut])
def list_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    return db.query(Leave).all()

@router.put("/{leave_id}/status", response_model=LeaveOut)
def update_leave_status(
    leave_id: int,
    status: LeaveStatusEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave record not found")

    old_status = leave.status
    leave.status = status
    db.commit()
    db.refresh(leave)

    log_activity(
        db=db,
        performed_by=current_user.email,
        action="LEAVE_STATUS_UPDATED",
        entity_type="Leave",
        entity_id=leave.id,
        details={
            "employee_id": leave.employee_id,
            "old_status": old_status.value,
            "new_status": status.value,
            "total_days": leave.total_days
        }
    )

    return leave
