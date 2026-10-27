import csv
import io
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Employee, User, Department, Attendance, RoleEnum
from app.core.security import get_password_hash
from app.api.deps import require_role
from app.services.audit import log_activity
from app.api.v1.predictions import evaluate_single_employee

router = APIRouter(prefix="/datasets", tags=["Module 11: Dataset Management System"])

class ImportSummary(BaseModel):
    total_rows: int
    successful_imports: int
    duplicates_skipped: int
    failed_records: int
    errors: List[str]

@router.post("/upload-csv", response_model=ImportSummary)
async def upload_employee_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "HR"]))
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a valid .csv file."
        )

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))
    required_cols = {"employee_code", "first_name", "last_name", "email", "department_code", "designation", "monthly_salary"}
    
    if not reader.fieldnames or not required_cols.issubset(set([c.strip() for c in reader.fieldnames])):
        missing = required_cols - set([c.strip() for c in (reader.fieldnames or [])])
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required CSV columns: {', '.join(missing)}"
        )

    # Cache existing departments
    departments = {d.code.upper(): d for d in db.query(Department).all()}
    
    total_rows = 0
    success_count = 0
    duplicate_count = 0
    failed_count = 0
    error_logs = []
    newly_added_employees = []

    for row_idx, row in enumerate(reader, start=2):
        total_rows += 1
        emp_code = (row.get("employee_code") or "").strip().upper()
        email = (row.get("email") or "").strip().lower()
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        dept_code = (row.get("department_code") or "").strip().upper()
        designation = (row.get("designation") or "").strip()
        salary_str = (row.get("monthly_salary") or "0").strip()
        doj_str = (row.get("date_of_joining") or "").strip()

        if not emp_code or not email or not first_name or not last_name:
            error_logs.append(f"Row {row_idx}: Essential fields missing (code/email/name).")
            failed_count += 1
            continue

        # Check duplicates
        if db.query(Employee).filter(Employee.employee_code == emp_code).first():
            duplicate_count += 1
            error_logs.append(f"Row {row_idx}: Employee code '{emp_code}' already exists. Skipped.")
            continue

        if db.query(User).filter(User.email == email).first():
            duplicate_count += 1
            error_logs.append(f"Row {row_idx}: Email '{email}' already registered. Skipped.")
            continue

        # Resolve department or create dynamically
        dept = departments.get(dept_code)
        if not dept:
            dept = Department(name=f"{dept_code} Division", code=dept_code, description="Auto-created from batch import")
            db.add(dept)
            db.flush()
            departments[dept_code] = dept

        try:
            salary = float(salary_str)
        except ValueError:
            salary = 50000.0

        try:
            date_of_joining = datetime.strptime(doj_str, "%Y-%m-%d").date() if doj_str else (date.today() - timedelta(days=180))
        except ValueError:
            date_of_joining = date.today() - timedelta(days=180)

        try:
            # 1. Create auth user
            user = User(
                email=email,
                hashed_password=get_password_hash("Password@123"),
                role=RoleEnum.EMPLOYEE
            )
            db.add(user)
            db.flush()

            # 2. Create employee profile
            emp = Employee(
                user_id=user.id,
                department_id=dept.id,
                employee_code=emp_code,
                first_name=first_name,
                last_name=last_name,
                phone=row.get("phone", "").strip() or None,
                designation=designation or "Associate",
                date_of_joining=date_of_joining,
                monthly_salary=salary
            )
            db.add(emp)
            db.flush()

            # 3. Seed baseline attendance (10 days)
            for day_offset in range(10):
                att = Attendance(
                    employee_id=emp.id,
                    date=date.today() - timedelta(days=day_offset),
                    total_hours=8.0
                )
                db.add(att)

            newly_added_employees.append(emp)
            success_count += 1
        except Exception as e:
            failed_count += 1
            error_logs.append(f"Row {row_idx}: Database commit failed: {str(e)}")

    db.commit()

    # Bulk recalculate risk predictions for newly added employees
    for emp in newly_added_employees:
        try:
            evaluate_single_employee(emp, db)
        except Exception:
            pass
    db.commit()

    # Log to operational audit trail
    log_activity(
        db=db,
        performed_by=current_user.email,
        action="BATCH_DATASET_IMPORTED",
        entity_type="Dataset",
        entity_id=file.filename,
        details={
            "total_rows": total_rows,
            "successful": success_count,
            "duplicates_skipped": duplicate_count,
            "failed": failed_count
        }
    )

    return ImportSummary(
        total_rows=total_rows,
        successful_imports=success_count,
        duplicates_skipped=duplicate_count,
        failed_records=failed_count,
        errors=error_logs[:10]
    )
