from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, EmailStr
from datetime import date
from app.core.database import get_db
from app.models.models import Employee, User, RoleEnum
from app.core.security import get_password_hash
from app.api.deps import require_role
from app.services.audit import log_activity

router = APIRouter(prefix="/employees", tags=["Module 3: Employee Management"])

class EmployeeCreate(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    department_id: int
    designation: str
    date_of_joining: date
    monthly_salary: float
    phone: str = None
    role: RoleEnum = RoleEnum.EMPLOYEE

class EmployeeOut(BaseModel):
    id: int
    employee_code: str
    first_name: str
    last_name: str
    designation: str
    department_id: int
    date_of_joining: date
    monthly_salary: float
    is_active: bool

    class Config:
        from_attributes = True

@router.post("/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(
    emp_in: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    if db.query(User).filter(User.email == emp_in.email).first():
        raise HTTPException(status_code=400, detail="User email already exists")
    if db.query(Employee).filter(Employee.employee_code == emp_in.employee_code).first():
        raise HTTPException(status_code=400, detail="Employee code already exists")

    new_user = User(
        email=emp_in.email,
        hashed_password=get_password_hash(emp_in.password),
        role=emp_in.role
    )
    db.add(new_user)
    db.flush()

    new_emp = Employee(
        user_id=new_user.id,
        department_id=emp_in.department_id,
        employee_code=emp_in.employee_code,
        first_name=emp_in.first_name,
        last_name=emp_in.last_name,
        phone=emp_in.phone,
        designation=emp_in.designation,
        date_of_joining=emp_in.date_of_joining,
        monthly_salary=emp_in.monthly_salary
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)

    log_activity(
        db=db,
        performed_by=current_user.email,
        action="EMPLOYEE_CREATED",
        entity_type="Employee",
        entity_id=new_emp.id,
        details={
            "code": new_emp.employee_code,
            "name": f"{new_emp.first_name} {new_emp.last_name}",
            "designation": new_emp.designation
        }
    )

    return new_emp

@router.get("/", response_model=List[EmployeeOut])
def list_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    return db.query(Employee).all()
