from datetime import date, datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Employee, Attendance, AttendanceStatusEnum, RoleEnum
from app.schemas import AttendanceOut, AttendanceOverride
from app.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api/attendance", tags=["Attendance Management"])


@router.post("/check-in", response_model=AttendanceOut)
def check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=400, detail="Employee profile not found for this user account")

    today = date.today()
    record = db.query(Attendance).filter(
        Attendance.employee_id == emp.id,
        Attendance.date == today
    ).first()

    if record and record.check_in:
        raise HTTPException(status_code=400, detail="Check-in already recorded for today")

    now = datetime.now(timezone.utc)
    if not record:
        record = Attendance(
            employee_id=emp.id,
            date=today,
            check_in=now,
            status=AttendanceStatusEnum.PRESENT
        )
        db.add(record)
    else:
        record.check_in = now

    db.commit()
    db.refresh(record)
    return record


@router.post("/check-out", response_model=AttendanceOut)
def check_out(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=400, detail="Employee profile not found")

    today = date.today()
    record = db.query(Attendance).filter(
        Attendance.employee_id == emp.id,
        Attendance.date == today
    ).first()

    if not record or not record.check_in:
        raise HTTPException(status_code=400, detail="Must check in before checking out")

    if record.check_out:
        raise HTTPException(status_code=400, detail="Check-out already completed for today")

    now = datetime.now(timezone.utc)
    record.check_out = now

    check_in_time = record.check_in
    if check_in_time.tzinfo is None:
        check_in_time = check_in_time.replace(tzinfo=timezone.utc)

    hours = round((now - check_in_time).total_seconds() / 3600, 2)
    record.total_hours = hours

    if hours < 4.0:
        record.status = AttendanceStatusEnum.ABSENT
    elif hours < 7.5:
        record.status = AttendanceStatusEnum.HALF_DAY
    else:
        record.status = AttendanceStatusEnum.PRESENT

    db.commit()
    db.refresh(record)
    return record


@router.get("/my-history", response_model=List[AttendanceOut])
def get_my_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        return []
    return db.query(Attendance).filter(Attendance.employee_id == emp.id).order_by(Attendance.date.desc()).all()


@router.put("/{attendance_id}/override", response_model=AttendanceOut)
def admin_override_attendance(
    attendance_id: int,
    payload: AttendanceOverride,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    record.status = payload.status
    record.total_hours = payload.total_hours
    record.is_manual_override = True
    record.override_reason = payload.reason

    db.commit()
    db.refresh(record)
    return record