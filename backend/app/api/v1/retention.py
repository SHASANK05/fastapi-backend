from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
from app.core.database import get_db
from app.models.models import RetentionCase, Employee, CaseStatusEnum, User, AttritionPrediction, Attendance, Leave
from app.api.deps import require_role
from app.services.audit import log_activity

router = APIRouter(prefix="/retention", tags=["Module 8: Retention Case Interventions"])

class RetentionCaseCreateOrUpdate(BaseModel):
    employee_id: int
    status: CaseStatusEnum
    priority: Optional[str] = "HIGH"
    action_plan: Optional[str] = None
    notes: Optional[str] = None

class RetentionCaseOut(BaseModel):
    id: int
    employee_id: int
    status: CaseStatusEnum
    priority: str
    action_plan: Optional[str]
    notes: Optional[str]
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class DiagnosticMetrics(BaseModel):
    employee_id: int
    employee_name: str
    employee_code: str
    designation: str
    department_name: str
    monthly_salary: float
    tenure_days: int
    avg_daily_hours: float
    overtime_days: int
    total_leaves_taken: int
    latest_risk_score: float
    primary_factor: str
    case: Optional[RetentionCaseOut]

@router.get("/diagnostics/{employee_id}", response_model=DiagnosticMetrics)
def get_retention_diagnostics(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    pred = db.query(AttritionPrediction).filter(
        AttritionPrediction.employee_id == employee_id
    ).order_by(AttritionPrediction.predicted_at.desc()).first()

    attendances = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
    avg_hours = sum(a.total_hours for a in attendances) / len(attendances) if attendances else 8.0
    ot_count = sum(1 for a in attendances if a.total_hours > 8.0)

    leaves = db.query(Leave).filter(Leave.employee_id == employee_id, Leave.status == "APPROVED").all()
    total_leave_days = sum(l.total_days for l in leaves)

    active_case = db.query(RetentionCase).filter(
        RetentionCase.employee_id == employee_id
    ).order_by(RetentionCase.updated_at.desc()).first()

    tenure = (date.today() - emp.date_of_joining).days

    return DiagnosticMetrics(
        employee_id=emp.id,
        employee_name=f"{emp.first_name} {emp.last_name}",
        employee_code=emp.employee_code,
        designation=emp.designation,
        department_name=emp.department.name if emp.department else "Unassigned",
        monthly_salary=emp.monthly_salary,
        tenure_days=tenure,
        avg_daily_hours=round(avg_hours, 1),
        overtime_days=ot_count,
        total_leaves_taken=total_leave_days,
        latest_risk_score=pred.risk_score if pred else 0.0,
        primary_factor=pred.top_contributing_factor if pred else "Normal Indicators",
        case=active_case
    )

@router.post("/save-case", response_model=RetentionCaseOut)
def save_or_update_case(
    payload: RetentionCaseCreateOrUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    emp = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing_case = db.query(RetentionCase).filter(RetentionCase.employee_id == payload.employee_id).first()

    if existing_case:
        existing_case.status = payload.status
        existing_case.priority = payload.priority or existing_case.priority
        existing_case.action_plan = payload.action_plan
        existing_case.notes = payload.notes
        existing_case.assigned_to = current_user.email
        case_obj = existing_case
        action_verb = "RETENTION_CASE_UPDATED"
    else:
        case_obj = RetentionCase(
            employee_id=payload.employee_id,
            status=payload.status,
            priority=payload.priority or "HIGH",
            action_plan=payload.action_plan,
            notes=payload.notes,
            assigned_to=current_user.email
        )
        db.add(case_obj)
        action_verb = "RETENTION_CASE_OPENED"

    db.commit()
    db.refresh(case_obj)

    log_activity(
        db=db,
        performed_by=current_user.email,
        action=action_verb,
        entity_type="RetentionCase",
        entity_id=case_obj.id,
        details={
            "employee_id": emp.id,
            "employee_code": emp.employee_code,
            "status": case_obj.status.value,
            "action_plan": case_obj.action_plan
        }
    )

    return case_obj
