import io
import csv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import date, datetime
from app.core.database import get_db
from app.models.models import Employee, Attendance, Leave, AttritionPrediction, RiskCategoryEnum, User, Department
from app.api.deps import require_role
from app.ml.predictor import get_predictor

router = APIRouter(prefix="/predictions", tags=["Module 6: Attrition AI Engine"])

class PredictionOut(BaseModel):
    id: int
    employee_id: int
    risk_score: float
    risk_category: RiskCategoryEnum
    confidence_level: float
    top_contributing_factor: str
    predicted_at: datetime

    class Config:
        from_attributes = True

class HighRiskEmployeeOut(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    designation: str
    department_id: int
    risk_score: float
    top_contributing_factor: str

class BulkPredictResult(BaseModel):
    evaluated_count: int
    high_risk_count: int
    moderate_risk_count: int
    low_risk_count: int
    timestamp: datetime

def evaluate_single_employee(employee: Employee, db: Session) -> AttritionPrediction:
    today = date.today()
    tenure_days = (today - employee.date_of_joining).days
    tenure_months = float(max(1.0, round(tenure_days / 30.4, 1)))

    total_leaves = db.query(func.coalesce(func.sum(Leave.total_days), 0)).filter(
        Leave.employee_id == employee.id
    ).scalar()
    total_leaves = int(total_leaves or 0)

    attendance_records = db.query(Attendance).filter(Attendance.employee_id == employee.id).all()
    if attendance_records:
        avg_hours = float(sum(r.total_hours for r in attendance_records) / len(attendance_records))
        overtime_count = sum(1 for r in attendance_records if r.total_hours > 9.0)
        overtime_freq = float(overtime_count / len(attendance_records))
    else:
        avg_hours = 8.0
        overtime_freq = 0.1

    input_payload = {
        "monthly_income": float(employee.monthly_salary),
        "total_leave_days": total_leaves,
        "avg_daily_hours": round(avg_hours, 2),
        "tenure_months": tenure_months,
        "overtime_frequency": round(overtime_freq, 2),
        "job_satisfaction_score": 3
    }

    predictor = get_predictor()
    result = predictor.predict_risk(input_payload)

    prediction_record = AttritionPrediction(
        employee_id=employee.id,
        risk_score=float(result["risk_score"]),
        risk_category=result["risk_category"],
        confidence_level=float(result["confidence_level"]),
        top_contributing_factor=str(result["top_contributing_factor"])
    )
    db.add(prediction_record)
    return prediction_record

@router.post("/predict/{employee_id}", response_model=PredictionOut, status_code=status.HTTP_201_CREATED)
def run_employee_prediction(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    record = evaluate_single_employee(employee, db)
    db.commit()
    db.refresh(record)
    return record

@router.post("/bulk-predict", response_model=BulkPredictResult)
def run_bulk_workforce_prediction(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    if not employees:
        raise HTTPException(status_code=400, detail="No active employees found to evaluate")

    low_cnt, mod_cnt, high_cnt = 0, 0, 0

    for emp in employees:
        pred = evaluate_single_employee(emp, db)
        if pred.risk_category == RiskCategoryEnum.HIGH:
            high_cnt += 1
        elif pred.risk_category == RiskCategoryEnum.MODERATE:
            mod_cnt += 1
        else:
            low_cnt += 1

    db.commit()

    return {
        "evaluated_count": len(employees),
        "high_risk_count": high_cnt,
        "moderate_risk_count": mod_cnt,
        "low_risk_count": low_cnt,
        "timestamp": datetime.now()
    }

@router.get("/high-risk", response_model=List[HighRiskEmployeeOut])
def get_high_risk_workforce(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    subquery = db.query(
        AttritionPrediction.employee_id,
        func.max(AttritionPrediction.id).label("max_id")
    ).group_by(AttritionPrediction.employee_id).subquery()

    records = db.query(AttritionPrediction, Employee).join(
        subquery, AttritionPrediction.id == subquery.c.max_id
    ).join(
        Employee, AttritionPrediction.employee_id == Employee.id
    ).filter(
        AttritionPrediction.risk_category == RiskCategoryEnum.HIGH
    ).all()

    return [
        {
            "employee_id": emp.id,
            "employee_code": emp.employee_code,
            "full_name": f"{emp.first_name} {emp.last_name}",
            "designation": emp.designation,
            "department_id": emp.department_id,
            "risk_score": pred.risk_score,
            "top_contributing_factor": pred.top_contributing_factor
        }
        for pred, emp in records
    ]

@router.get("/analytics")
def get_workforce_risk_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    subquery = db.query(
        AttritionPrediction.employee_id,
        func.max(AttritionPrediction.id).label("max_id")
    ).group_by(AttritionPrediction.employee_id).subquery()

    latest_preds = db.query(AttritionPrediction).join(
        subquery, AttritionPrediction.id == subquery.c.max_id
    ).all()

    total_predictions = len(latest_preds)
    low_count = sum(1 for p in latest_preds if p.risk_category == RiskCategoryEnum.LOW)
    mod_count = sum(1 for p in latest_preds if p.risk_category == RiskCategoryEnum.MODERATE)
    high_count = sum(1 for p in latest_preds if p.risk_category == RiskCategoryEnum.HIGH)

    return {
        "total_workforce_evaluated": total_predictions,
        "distribution": {
            "low_risk": low_count,
            "moderate_risk": mod_count,
            "high_risk": high_count
        },
        "critical_alert": high_count > 0
    }

@router.get("/department-risk")
def get_department_risk_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR", "MANAGER"]))
):
    departments = db.query(Department).all()
    breakdown = []

    subquery = db.query(
        AttritionPrediction.employee_id,
        func.max(AttritionPrediction.id).label("max_id")
    ).group_by(AttritionPrediction.employee_id).subquery()

    for dept in departments:
        dept_preds = db.query(AttritionPrediction).join(
            subquery, AttritionPrediction.id == subquery.c.max_id
        ).join(
            Employee, AttritionPrediction.employee_id == Employee.id
        ).filter(
            Employee.department_id == dept.id
        ).all()

        total = len(dept_preds)
        avg_score = round(sum(p.risk_score for p in dept_preds) / total, 2) if total > 0 else 0.0
        high_risk_num = sum(1 for p in dept_preds if p.risk_category == RiskCategoryEnum.HIGH)

        breakdown.append({
            "department_id": dept.id,
            "department_name": dept.name,
            "department_code": dept.code,
            "employee_count": total,
            "average_risk_score": avg_score,
            "high_risk_count": high_risk_num
        })

    return breakdown

@router.get("/export-csv")
def export_workforce_predictions_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    subquery = db.query(
        AttritionPrediction.employee_id,
        func.max(AttritionPrediction.id).label("max_id")
    ).group_by(AttritionPrediction.employee_id).subquery()

    records = db.query(
        Employee, Department, AttritionPrediction
    ).outerjoin(
        Department, Employee.department_id == Department.id
    ).outerjoin(
        subquery, Employee.id == subquery.c.employee_id
    ).outerjoin(
        AttritionPrediction, AttritionPrediction.id == subquery.c.max_id
    ).filter(
        Employee.is_active == True
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Employee ID",
        "Employee Code",
        "Full Name",
        "Department Code",
        "Department Name",
        "Designation",
        "Date of Joining",
        "Monthly Salary (INR)",
        "Risk Score (%)",
        "Risk Category",
        "Confidence (%)",
        "Top Contributing Factor",
        "Last Evaluated At"
    ])

    for emp, dept, pred in records:
        writer.writerow([
            emp.id,
            emp.employee_code,
            f"{emp.first_name} {emp.last_name}",
            dept.code if dept else "N/A",
            dept.name if dept else "N/A",
            emp.designation,
            emp.date_of_joining.strftime("%Y-%m-%d"),
            emp.monthly_salary,
            pred.risk_score if pred else "Unscored",
            pred.risk_category.value if pred else "Unscored",
            pred.confidence_level if pred else "N/A",
            pred.top_contributing_factor if pred else "N/A",
            pred.predicted_at.strftime("%Y-%m-%d %H:%M:%S") if pred else "N/A"
        ])

    output.seek(0)
    filename = f"workforce_attrition_report_{date.today().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# --- Background Scheduler Control Routes ---
from app.services.scheduler import scheduler, run_nightly_attrition_recalculation
from fastapi import BackgroundTasks

@router.get("/scheduler/status")
def get_scheduler_status(
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None
        })
    return {
        "scheduler_running": scheduler.running,
        "active_jobs": jobs
    }

@router.post("/scheduler/run-now")
def trigger_scheduled_job_now(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    background_tasks.add_task(run_nightly_attrition_recalculation)
    return {
        "status": "triggered",
        "message": "Background recalculation dispatched asynchronously."
    }
