from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Employee, RoleEnum,
    LeaveType, LeaveBalance, LeaveRequest, LeaveStatusEnum
)
from app.schemas import (
    LeaveTypeCreate, LeaveTypeOut,
    LeaveBalanceOut,
    LeaveRequestCreate, LeaveRequestOut, LeaveReviewAction
)
from app.dependencies import get_current_user, require_roles
from app.services.notifications import NotificationService

router = APIRouter(prefix="/api/leaves", tags=["Leave Management"])


# --- Leave Types (Admin / HR) ---

@router.post("/types", response_model=LeaveTypeOut, status_code=status.HTTP_201_CREATED)
def create_leave_type(
    payload: LeaveTypeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    existing = db.query(LeaveType).filter(
        (LeaveType.code == payload.code.upper()) | (LeaveType.name == payload.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Leave type with this name or code already exists")

    leave_type = LeaveType(
        name=payload.name,
        code=payload.code.upper(),
        default_days_per_year=payload.default_days_per_year
    )
    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)
    return leave_type


@router.get("/types", response_model=List[LeaveTypeOut])
def list_leave_types(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    return db.query(LeaveType).all()


# --- Balances ---

@router.get("/my-balances", response_model=List[LeaveBalanceOut])
def get_my_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        return []
    
    current_year = date.today().year
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == emp.id,
        LeaveBalance.year == current_year
    ).all()

    # Auto-initialize balances if not seeded yet
    if not balances:
        all_types = db.query(LeaveType).all()
        for lt in all_types:
            new_bal = LeaveBalance(
                employee_id=emp.id,
                leave_type_id=lt.id,
                year=current_year,
                total_days=float(lt.default_days_per_year),
                used_days=0.0
            )
            db.add(new_bal)
        db.commit()
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == emp.id,
            LeaveBalance.year == current_year
        ).all()

    return balances


# --- Leave Requests ---

@router.post("/apply", response_model=LeaveRequestOut, status_code=status.HTTP_201_CREATED)
def apply_leave(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=400, detail="Employee profile not found")

    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be prior to start date")

    days = (payload.end_date - payload.start_date).days + 1

    current_year = payload.start_date.year
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == emp.id,
        LeaveBalance.leave_type_id == payload.leave_type_id,
        LeaveBalance.year == current_year
    ).first()

    if balance and (balance.total_days - balance.used_days) < days:
        raise HTTPException(status_code=400, detail="Insufficient leave balance for this request")

    leave_req = LeaveRequest(
        employee_id=emp.id,
        leave_type_id=payload.leave_type_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days_count=float(days),
        reason=payload.reason,
        status=LeaveStatusEnum.PENDING
    )
    db.add(leave_req)
    db.commit()
    db.refresh(leave_req)
    return leave_req


@router.get("/my-requests", response_model=List[LeaveRequestOut])
def get_my_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        return []
    return db.query(LeaveRequest).filter(LeaveRequest.employee_id == emp.id).order_by(LeaveRequest.created_at.desc()).all()


@router.get("/all", response_model=List[LeaveRequestOut])
def get_all_leave_requests(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    return db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()


@router.put("/{request_id}/review", response_model=LeaveRequestOut)
def review_leave_request(
    request_id: int,
    payload: LeaveReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if req.status != LeaveStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already resolved as {req.status.value}")

    req.status = payload.status
    req.reviewer_id = current_user.id
    req.review_comments = payload.comments

    # Deduct balance if approved
    if payload.status == LeaveStatusEnum.APPROVED:
        bal = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == req.employee_id,
            LeaveBalance.leave_type_id == req.leave_type_id,
            LeaveBalance.year == req.start_date.year
        ).first()
        if bal:
            bal.used_days += req.days_count

    db.commit()
    db.refresh(req)

    # Trigger notification
    try:
        emp = req.employee
        lt = req.leave_type
        emp_email = emp.email if hasattr(emp, "email") and emp.email else (emp.user.email if hasattr(emp, "user") and emp.user else "")
        emp_name = f"{emp.first_name} {emp.last_name}" if emp else "Employee"
        lt_name = lt.name if lt else "Leave"

        if emp_email:
            NotificationService.notify_leave_status(
                emp_email=emp_email,
                emp_name=emp_name,
                leave_type=lt_name,
                status=req.status.value if hasattr(req.status, "value") else str(req.status),
                approver_comment=payload.comments
            )
    except Exception as e:
        print(f"Notification error: {e}")

    return req