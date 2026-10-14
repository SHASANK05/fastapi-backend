import csv
import io
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Employee, Attendance, LeaveRequest, LeaveType, Payroll, Department, RoleEnum
from app.dependencies import require_roles

router = APIRouter(prefix="/api/reports", tags=["Reports & Analytics"])


@router.get("/attendance/csv")
def export_attendance_csv(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    query = db.query(Attendance).join(Employee, Attendance.employee_id == Employee.id)

    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    if department_id:
        query = query.filter(Employee.department_id == department_id)

    records = query.order_by(Attendance.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record ID", "Employee Code", "Employee Name", "Date",
        "Check-In", "Check-Out", "Working Hours", "Status"
    ])

    for r in records:
        emp = r.employee
        writer.writerow([
            r.id,
            emp.emp_code if emp else "N/A",
            f"{emp.first_name} {emp.last_name}" if emp else "N/A",
            r.date.isoformat(),
            r.check_in.strftime("%H:%M:%S") if r.check_in else "",
            r.check_out.strftime("%H:%M:%S") if r.check_out else "",
            round(r.total_hours, 2) if r.total_hours else 0.0,
            r.status.value if r.status else ""
        ])

    output.seek(0)
    filename = f"attendance_report_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/leaves/csv")
def export_leaves_csv(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    query = db.query(LeaveRequest).join(Employee, LeaveRequest.employee_id == Employee.id)

    if status:
        query = query.filter(LeaveRequest.status == status.upper())

    records = query.order_by(LeaveRequest.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Request ID", "Employee Code", "Employee Name", "Leave Type",
        "Start Date", "End Date", "Days", "Status", "Reason"
    ])

    for r in records:
        emp = r.employee
        lt = db.query(LeaveType).filter(LeaveType.id == r.leave_type_id).first()
        writer.writerow([
            r.id,
            emp.emp_code if emp else "N/A",
            f"{emp.first_name} {emp.last_name}" if emp else "N/A",
            lt.name if lt else "N/A",
            r.start_date.isoformat(),
            r.end_date.isoformat(),
            r.days_count,
            r.status.value,
            r.reason or ""
        ])

    output.seek(0)
    filename = f"leaves_report_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/payroll/csv")
def export_payroll_csv(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    records = db.query(Payroll).join(Employee, Payroll.employee_id == Employee.id).filter(
        Payroll.month == month,
        Payroll.year == year
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail="No payroll records found for this period")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Payroll ID", "Employee Code", "Employee Name", "Month", "Year",
        "Base Salary", "Allowances", "Deductions", "LOP Days", "LOP Amount",
        "Net Salary", "Locked Status"
    ])

    for p in records:
        emp = p.employee
        writer.writerow([
            p.id,
            emp.emp_code if emp else "N/A",
            f"{emp.first_name} {emp.last_name}" if emp else "N/A",
            p.month,
            p.year,
            float(p.base_salary),
            float(p.allowances),
            float(p.deductions),
            p.lop_days,
            float(p.lop_amount),
            float(p.net_salary),
            "Locked" if p.is_locked else "Draft"
        ])

    output.seek(0)
    filename = f"payroll_register_{month}_{year}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )