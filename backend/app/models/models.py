from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    HR = "HR"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"

class LeaveTypeEnum(str, enum.Enum):
    CASUAL = "CASUAL"
    SICK = "SICK"
    EMERGENCY = "EMERGENCY"
    UNPAID = "UNPAID"

class LeaveStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class AttendanceStatusEnum(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"

class RiskCategoryEnum(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"

class CaseStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACTION_PLANNED = "ACTION_PLANNED"
    RESOLVED = "RESOLVED"
    LOST = "LOST"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.EMPLOYEE, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="user", uselist=False)

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    designation = Column(String(100), nullable=False)
    date_of_joining = Column(Date, nullable=False)
    monthly_salary = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    attendances = relationship("Attendance", back_populates="employee")
    leaves = relationship("Leave", back_populates="employee")
    predictions = relationship("AttritionPrediction", back_populates="employee")
    retention_cases = relationship("RetentionCase", back_populates="employee")

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    total_hours = Column(Float, default=0.0)
    status = Column(Enum(AttendanceStatusEnum), default=AttendanceStatusEnum.PRESENT)

    employee = relationship("Employee", back_populates="attendances")

class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(Enum(LeaveTypeEnum), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    status = Column(Enum(LeaveStatusEnum), default=LeaveStatusEnum.PENDING)
    reason = Column(String(255), nullable=True)

    employee = relationship("Employee", back_populates="leaves")

class AttritionPrediction(Base):
    __tablename__ = "attrition_predictions"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_category = Column(Enum(RiskCategoryEnum), nullable=False)
    confidence_level = Column(Float, nullable=False)
    top_contributing_factor = Column(String(255), nullable=False)
    predicted_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="predictions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    performed_by = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class RetentionCase(Base):
    __tablename__ = "retention_cases"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    status = Column(Enum(CaseStatusEnum), default=CaseStatusEnum.OPEN, nullable=False)
    priority = Column(String(20), default="HIGH", nullable=False)
    action_plan = Column(String(255), nullable=True) # e.g. "Compensation Review", "1-on-1 Mentorship", "Role Rotation"
    notes = Column(Text, nullable=True)
    assigned_to = Column(String(100), nullable=True) # HR reviewer email
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="retention_cases")
