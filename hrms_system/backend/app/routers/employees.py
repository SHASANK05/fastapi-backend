import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Employee, Department, Document, RoleEnum, DocumentTypeEnum
from app.schemas import (
    DepartmentCreate, DepartmentOut, 
    EmployeeCreate, EmployeeOut, EmployeeUpdate,
    DocumentOut
)
from app.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["Employees & Departments"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# --- DEPARTMENTS ---

@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    existing = db.query(Department).filter(
        (Department.name == payload.name) | (Department.code == payload.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department name or code already exists")

    dept = Department(name=payload.name, code=payload.code.upper())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    return db.query(Department).all()


# --- EMPLOYEES ---

@router.post("/employees", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee_profile(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User account not found")

    existing_profile = db.query(Employee).filter(
        (Employee.user_id == payload.user_id) | (Employee.emp_code == payload.emp_code)
    ).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Employee code or profile already exists for this user")

    emp = Employee(**payload.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.get("/employees", response_model=List[EmployeeOut])
def list_employees(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    return db.query(Employee).offset(skip).limit(limit).all()


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role == RoleEnum.EMPLOYEE and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to profile")

    return emp


@router.put("/employees/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.HR))
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(emp, field, value)

    db.commit()
    db.refresh(emp)
    return emp


# --- DOCUMENT UPLOADS ---

@router.post("/employees/{employee_id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_employee_document(
    employee_id: int,
    doc_type: DocumentTypeEnum = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role == RoleEnum.EMPLOYEE and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized upload attempt")

    safe_filename = f"emp_{emp.id}_{doc_type.value}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc_record = Document(
        employee_id=emp.id,
        doc_type=doc_type,
        filename=safe_filename,
        file_path=file_path
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)
    return doc_record
