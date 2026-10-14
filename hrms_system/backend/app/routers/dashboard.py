from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Employee, Attendance, AttendanceStatusEnum, LeaveRequest, LeaveStatusEnum, Payroll, RoleEnum
from app.dependencies import require_roles

router = APIRouter(prefix="/api/dashboard", tags=["Admin Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    today = date.today()
    current_month = today.month
    current_year = today.year

    # 1. Total headcount
    total_employees = db.query(func.count(Employee.id)).scalar() or 0

    # 2. Active employees checking: inspect attribute on Employee or linked User
    if hasattr(Employee, "is_active"):
        active_employees = db.query(func.count(Employee.id)).filter(Employee.is_active == True).scalar() or 0
    elif hasattr(Employee, "status"):
        active_employees = db.query(func.count(Employee.id)).filter(func.upper(Employee.status) == "ACTIVE").scalar() or 0
    elif hasattr(Employee, "user_id"):
        # Check active status via linked user account
        active_employees = db.query(func.count(Employee.id)).join(User, Employee.user_id == User.id).filter(User.is_active == True).scalar() or 0
    else:
        active_employees = total_employees

    # 3. Today's attendance
    present_today = db.query(func.count(Attendance.id)).filter(
        Attendance.date == today,
        Attendance.status.in_([AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.HALF_DAY])
    ).scalar() or 0

    absent_today = max(0, total_employees - present_today)

    # 4. Pending leave requests
    pending_leaves = db.query(func.count(LeaveRequest.id)).filter(
        LeaveRequest.status == LeaveStatusEnum.PENDING
    ).scalar() or 0

    # 5. Total payroll expenditure for current month
    payroll_total = db.query(func.sum(Payroll.net_salary)).filter(
        Payroll.month == current_month,
        Payroll.year == current_year
    ).scalar() or 0.0

    return {
        "employees": {
            "total": total_employees,
            "active": active_employees,
            "inactive": max(0, total_employees - active_employees)
        },
        "today_attendance": {
            "date": today.isoformat(),
            "present": present_today,
            "absent": absent_today
        },
        "leaves": {
            "pending_approval": pending_leaves
        },
        "payroll": {
            "month": current_month,
            "year": current_year,
            "total_disbursed": float(payroll_total)
        }
    }