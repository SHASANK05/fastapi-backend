from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from collections import Counter
from app.core.database import get_db
from app.models.models import Department, Employee, AttritionPrediction, User
from app.api.deps import require_role

router = APIRouter(prefix="/departments", tags=["Module 2: Department Management"])

class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class DepartmentOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]

    class Config:
        from_attributes = True

class DeptEmployeeSummary(BaseModel):
    id: int
    employee_code: str
    full_name: str
    designation: str
    monthly_salary: float
    tenure_days: int
    risk_score: float
    risk_category: str
    top_contributing_factor: str

class DepartmentDeepDive(BaseModel):
    department_id: int
    name: str
    code: str
    description: Optional[str]
    headcount: int
    average_salary: float
    average_risk_score: float
    high_risk_count: int
    moderate_risk_count: int
    low_risk_count: int
    primary_team_driver: str
    employees: List[DeptEmployeeSummary]

@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    if db.query(Department).filter(Department.code == dept_in.code).first():
        raise HTTPException(status_code=400, detail="Department code already exists")
    new_dept = Department(name=dept_in.name, code=dept_in.code, description=dept_in.description)
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept

@router.get("/", response_model=List[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    return db.query(Department).all()

@router.get("/{dept_code}/deep-dive", response_model=DepartmentDeepDive)
def get_department_deep_dive(
    dept_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    dept = db.query(Department).filter(Department.code == dept_code).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    emps = db.query(Employee).filter(Employee.department_id == dept.id, Employee.is_active == True).all()
    if not emps:
        return DepartmentDeepDive(
            department_id=dept.id,
            name=dept.name,
            code=dept.code,
            description=dept.description,
            headcount=0,
            average_salary=0.0,
            average_risk_score=0.0,
            high_risk_count=0,
            moderate_risk_count=0,
            low_risk_count=0,
            primary_team_driver="No active employees",
            employees=[]
        )

    emp_summaries = []
    scores = []
    drivers = []
    high_c, mod_c, low_c = 0, 0, 0

    for emp in emps:
        pred = db.query(AttritionPrediction).filter(
            AttritionPrediction.employee_id == emp.id
        ).order_by(AttritionPrediction.predicted_at.desc()).first()

        score = pred.risk_score if pred else 0.0
        cat = pred.risk_category.value if pred else "LOW"
        driver = pred.top_contributing_factor if pred else "Normal Indicators"

        if cat == "HIGH":
            high_c += 1
        elif cat == "MODERATE":
            mod_c += 1
        else:
            low_c += 1

        scores.append(score)
        if pred and pred.top_contributing_factor != "Normal Indicators":
            drivers.append(pred.top_contributing_factor)

        tenure = (date.today() - emp.date_of_joining).days
        emp_summaries.append(DeptEmployeeSummary(
            id=emp.id,
            employee_code=emp.employee_code,
            full_name=f"{emp.first_name} {emp.last_name}",
            designation=emp.designation,
            monthly_salary=emp.monthly_salary,
            tenure_days=tenure,
            risk_score=score,
            risk_category=cat,
            top_contributing_factor=driver
        ))

    most_common_driver = Counter(drivers).most_common(1)[0][0] if drivers else "Stable Baseline"
    avg_sal = sum(e.monthly_salary for e in emps) / len(emps)
    avg_risk = sum(scores) / len(scores) if scores else 0.0

    return DepartmentDeepDive(
        department_id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        headcount=len(emps),
        average_salary=round(avg_sal, 2),
        average_risk_score=round(avg_risk, 1),
        high_risk_count=high_c,
        moderate_risk_count=mod_c,
        low_risk_count=low_c,
        primary_team_driver=most_common_driver,
        employees=emp_summaries
    )
