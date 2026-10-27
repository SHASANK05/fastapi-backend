from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from app.core.database import get_db
from app.models.models import Attendance, Employee, User
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/attendance", tags=["Module 4: Attendance Tracking"])

class AttendanceOut(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in: str
    check_out: Optional[str] = None
    total_hours: float
    status: str

    class Config:
        from_attributes = True

@router.post("/clock-in", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def clock_in(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=400, detail="Authenticated user is not linked to an employee profile")

    today = date.today()
    existing_record = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today
    ).first()

    if existing_record:
        raise HTTPException(status_code=400, detail="Already clocked in for today")

    now = datetime.now().time()
    attendance = Attendance(
        employee_id=employee.id,
        date=today,
        check_in=now,
        status="PRESENT"
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return {
        "id": attendance.id,
        "employee_id": attendance.employee_id,
        "date": attendance.date,
        "check_in": attendance.check_in.strftime("%H:%M:%S"),
        "check_out": None,
        "total_hours": attendance.total_hours,
        "status": attendance.status
    }

@router.post("/clock-out", response_model=AttendanceOut)
def clock_out(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=400, detail="Authenticated user is not linked to an employee profile")

    today = date.today()
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today
    ).first()

    if not attendance:
        raise HTTPException(status_code=400, detail="No active clock-in found for today. Please clock in first.")
    if attendance.check_out:
        raise HTTPException(status_code=400, detail="Already clocked out for today")

    now_dt = datetime.now()
    attendance.check_out = now_dt.time()

    in_datetime = datetime.combine(today, attendance.check_in)
    out_datetime = datetime.combine(today, attendance.check_out)
    diff = (out_datetime - in_datetime).total_seconds() / 3600.0
    attendance.total_hours = round(diff, 2)

    db.commit()
    db.refresh(attendance)

    return {
        "id": attendance.id,
        "employee_id": attendance.employee_id,
        "date": attendance.date,
        "check_in": attendance.check_in.strftime("%H:%M:%S"),
        "check_out": attendance.check_out.strftime("%H:%M:%S"),
        "total_hours": attendance.total_hours,
        "status": attendance.status
    }

@router.get("/my-records", response_model=List[AttendanceOut])
def get_my_attendance(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=400, detail="Authenticated user is not linked to an employee profile")

    records = db.query(Attendance).filter(Attendance.employee_id == employee.id).order_by(Attendance.date.desc()).all()
    return [
        {
            "id": r.id,
            "employee_id": r.employee_id,
            "date": r.date,
            "check_in": r.check_in.strftime("%H:%M:%S"),
            "check_out": r.check_out.strftime("%H:%M:%S") if r.check_out else None,
            "total_hours": r.total_hours,
            "status": r.status
        }
        for r in records
    ]

@router.get("/all", response_model=List[AttendanceOut])
def list_all_attendance(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    query = db.query(Attendance)
    if target_date:
        query = query.filter(Attendance.date == target_date)
    records = query.order_by(Attendance.date.desc()).all()
    return [
        {
            "id": r.id,
            "employee_id": r.employee_id,
            "date": r.date,
            "check_in": r.check_in.strftime("%H:%M:%S"),
            "check_out": r.check_out.strftime("%H:%M:%S") if r.check_out else None,
            "total_hours": r.total_hours,
            "status": r.status
        }
        for r in records
    ]
