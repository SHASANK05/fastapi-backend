from datetime import date, datetime
from pydantic import BaseModel, EmailStr
from app.models import RoleEnum, EmployeeStatusEnum
from app.models import DocumentTypeEnum
from app.models import AttendanceStatusEnum
from app.models import LeaveStatusEnum

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.EMPLOYEE


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    name: str
    code: str


class DepartmentOut(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    user_id: int
    emp_code: str
    first_name: str
    last_name: str
    phone: str | None = None
    department_id: int | None = None
    designation: str
    joining_date: date
    base_salary: float


class EmployeeOut(BaseModel):
    id: int
    emp_code: str
    first_name: str
    last_name: str
    phone: str | None
    designation: str
    joining_date: date
    base_salary: float
    status: EmployeeStatusEnum
    department: DepartmentOut | None

    class Config:
        from_attributes = True

class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    department_id: int | None = None
    designation: str | None = None
    base_salary: float | None = None
    status: EmployeeStatusEnum | None = None


class DocumentOut(BaseModel):
    id: int
    employee_id: int
    doc_type: DocumentTypeEnum
    filename: str
    uploaded_at: datetime

    class Config:
        from_attributes = True        

class AttendanceOut(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    total_hours: float
    status: AttendanceStatusEnum
    is_manual_override: bool
    override_reason: str | None = None

    class Config:
        from_attributes = True


class AttendanceOverride(BaseModel):
    status: AttendanceStatusEnum
    total_hours: float
    reason: str        


class LeaveTypeCreate(BaseModel):
    name: str
    code: str
    default_days_per_year: int = 12


class LeaveTypeOut(LeaveTypeCreate):
    id: int

    class Config:
        from_attributes = True


class LeaveBalanceOut(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    year: int
    total_days: float
    used_days: float
    leave_type: LeaveTypeOut

    class Config:
        from_attributes = True


class LeaveRequestCreate(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str


class LeaveRequestOut(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    days_count: float
    reason: str
    status: LeaveStatusEnum
    reviewer_id: int | None = None
    review_comments: str | None = None

    class Config:
        from_attributes = True


class LeaveReviewAction(BaseModel):
    status: LeaveStatusEnum  # APPROVED or REJECTED
    comments: str | None = None    

class PayrollGenerateRequest(BaseModel):
    employee_id: int
    month: int
    year: int
    allowances: float = 0.00
    deductions: float = 0.00


class PayrollOut(BaseModel):
    id: int
    employee_id: int
    month: int
    year: int
    base_salary: float
    allowances: float
    deductions: float
    lop_days: float
    lop_amount: float
    net_salary: float
    is_locked: bool

    class Config:
        from_attributes = True    