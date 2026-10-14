import io
import calendar
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.database import get_db
from app.models import User, Employee, Payroll, RoleEnum
from app.schemas import PayrollGenerateRequest, PayrollOut
from app.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api/payroll", tags=["Payroll Management"])


@router.post("/generate", response_model=PayrollOut, status_code=status.HTTP_201_CREATED)
def generate_payroll(
    payload: PayrollGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    emp = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing = db.query(Payroll).filter(
        Payroll.employee_id == payload.employee_id,
        Payroll.month == payload.month,
        Payroll.year == payload.year
    ).first()

    if existing and existing.is_locked:
        raise HTTPException(status_code=400, detail="Payroll for this period is finalized and locked")

    base = float(emp.base_salary)
    days_in_month = calendar.monthrange(payload.year, payload.month)[1]
    per_day_salary = base / days_in_month

    lop_days = 0.0
    lop_amount = lop_days * per_day_salary
    net = round(base + payload.allowances - payload.deductions - lop_amount, 2)

    if existing:
        existing.base_salary = base
        existing.allowances = payload.allowances
        existing.deductions = payload.deductions
        existing.lop_days = lop_days
        existing.lop_amount = lop_amount
        existing.net_salary = net
        payroll_entry = existing
    else:
        payroll_entry = Payroll(
            employee_id=emp.id,
            month=payload.month,
            year=payload.year,
            base_salary=base,
            allowances=payload.allowances,
            deductions=payload.deductions,
            lop_days=lop_days,
            lop_amount=lop_amount,
            net_salary=net,
            is_locked=False
        )
        db.add(payroll_entry)

    db.commit()
    db.refresh(payroll_entry)
    return payroll_entry


@router.put("/{payroll_id}/lock", response_model=PayrollOut)
def lock_payroll(
    payroll_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    entry = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    entry.is_locked = True
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/my-slips", response_model=List[PayrollOut])
def get_my_slips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        return []
    return db.query(Payroll).filter(Payroll.employee_id == emp.id).order_by(Payroll.year.desc(), Payroll.month.desc()).all()


@router.get("/{payroll_id}/download-pdf")
def download_payslip_pdf(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    emp = db.query(Employee).filter(Employee.id == entry.employee_id).first()
    if current_user.role == RoleEnum.EMPLOYEE and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to download this payslip")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "STACKLY HRMS - SALARY PAYSLIP")
    p.setFont("Helvetica", 10)
    p.drawString(100, 735, f"Pay Period: {calendar.month_name[entry.month]} {entry.year}")

    p.line(100, 720, 500, 720)

    p.drawString(100, 690, f"Employee Name: {emp.first_name} {emp.last_name}")
    p.drawString(100, 670, f"Employee Code: {emp.emp_code}")
    p.drawString(100, 650, f"Designation: {emp.designation}")

    p.line(100, 630, 500, 630)

    p.drawString(100, 600, f"Base Salary: Rs. {entry.base_salary:,.2f}")
    p.drawString(100, 580, f"Allowances: Rs. {entry.allowances:,.2f}")
    p.drawString(100, 560, f"Deductions: Rs. {entry.deductions:,.2f}")
    p.drawString(100, 540, f"Loss of Pay (LOP): Rs. {entry.lop_amount:,.2f}")

    p.line(100, 520, 500, 520)

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 490, f"Net Payable Salary: Rs. {entry.net_salary:,.2f}")
    p.setFont("Helvetica", 9)
    p.drawString(100, 460, "This is an electronically generated salary slip.")

    p.showPage()
    p.save()

    buffer.seek(0)
    filename = f"Payslip_{emp.emp_code}_{entry.month}_{entry.year}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )