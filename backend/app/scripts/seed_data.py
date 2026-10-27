import random
from datetime import date, datetime, time, timedelta
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.models import (
    User, Department, Employee, Attendance, Leave,
    RoleEnum, LeaveTypeEnum, LeaveStatusEnum
)

def seed():
    db = SessionLocal()
    try:
        print("Seeding workforce intelligence data...")

        # 1. Departments
        dept_data = [
            {"name": "Engineering", "code": "ENG", "budget": 3500000.0},
            {"name": "Human Resources", "code": "HR", "budget": 950000.0},
            {"name": "Sales & Marketing", "code": "MKT", "budget": 2100000.0},
            {"name": "Customer Operations", "code": "OPS", "budget": 1400000.0},
        ]
        departments = []
        for d in dept_data:
            dept = db.query(Department).filter(Department.code == d["code"]).first()
            if not dept:
                dept = Department(**d)
                db.add(dept)
                db.commit()
                db.refresh(dept)
            departments.append(dept)

        # 2. Diverse Workforce Archetypes (Low, Moderate, and High Attrition Profiles)
        profiles = [
            # High Risk Archetypes (Heavy overtime, high leave frequency, lower relative pay)
            {"first": "Vikram", "last": "Rao", "role": RoleEnum.EMPLOYEE, "dept": departments[0], "code": "EMP002", "desig": "DevOps Engineer", "salary": 45000.0, "doj": date(2025, 4, 1), "overtime": True, "heavy_leaves": True},
            {"first": "Priya", "last": "Nair", "role": RoleEnum.EMPLOYEE, "dept": departments[2], "code": "EMP003", "desig": "Sales Executive", "salary": 38000.0, "doj": date(2025, 8, 10), "overtime": True, "heavy_leaves": True},
            {"first": "Karan", "last": "Malhotra", "role": RoleEnum.EMPLOYEE, "dept": departments[3], "code": "EMP004", "desig": "Support Associate", "salary": 32000.0, "doj": date(2025, 11, 1), "overtime": True, "heavy_leaves": False},
            
            # Moderate Risk Archetypes
            {"first": "Ananya", "last": "Deshmukh", "role": RoleEnum.MANAGER, "dept": departments[0], "code": "EMP005", "desig": "Engineering Manager", "salary": 145000.0, "doj": date(2023, 6, 1), "overtime": True, "heavy_leaves": False},
            {"first": "Suresh", "last": "Pillai", "role": RoleEnum.EMPLOYEE, "dept": departments[3], "code": "EMP006", "desig": "Operations Lead", "salary": 68000.0, "doj": date(2024, 2, 15), "overtime": False, "heavy_leaves": True},
            
            # Low Risk / Retained Archetypes
            {"first": "Divya", "last": "Iyer", "role": RoleEnum.HR, "dept": departments[1], "code": "EMP007", "desig": "HR Business Partner", "salary": 92000.0, "doj": date(2022, 1, 10), "overtime": False, "heavy_leaves": False},
            {"first": "Rohan", "last": "Verma", "role": RoleEnum.EMPLOYEE, "dept": departments[0], "code": "EMP008", "desig": "Senior Backend Architect", "salary": 185000.0, "doj": date(2021, 3, 20), "overtime": False, "heavy_leaves": False},
            {"first": "Sneha", "last": "Kulkarni", "role": RoleEnum.EMPLOYEE, "dept": departments[2], "code": "EMP009", "desig": "Brand Strategist", "salary": 85000.0, "doj": date(2023, 9, 1), "overtime": False, "heavy_leaves": False},
        ]

        today = date.today()

        for p in profiles:
            email = f"{p['first'].lower()}.{p['last'].lower()}@workforce.ai"
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=get_password_hash("Password@123"),
                    role=p["role"]
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            emp = db.query(Employee).filter(Employee.employee_code == p["code"]).first()
            if not emp:
                emp = Employee(
                    user_id=user.id,
                    department_id=p["dept"].id,
                    employee_code=p["code"],
                    first_name=p["first"],
                    last_name=p["last"],
                    designation=p["desig"],
                    date_of_joining=p["doj"],
                    monthly_salary=p["salary"],
                    phone=f"+91{random.randint(7000000000, 9999999999)}"
                )
                db.add(emp)
                db.commit()
                db.refresh(emp)

                # Seed 14 Days Attendance History
                for day_offset in range(14, 0, -1):
                    rec_date = today - timedelta(days=day_offset)
                    if rec_date.weekday() >= 5:  # Skip weekends
                        continue
                    
                    if p["overtime"]:
                        hours = round(random.uniform(9.5, 12.0), 2)
                    else:
                        hours = round(random.uniform(7.8, 8.5), 2)

                    att = Attendance(
                        employee_id=emp.id,
                        date=rec_date,
                        check_in=time(9, 0, 0),
                        check_out=time(int(9 + hours), int((hours % 1) * 60), 0),
                        total_hours=hours,
                        status="PRESENT"
                    )
                    db.add(att)

                # Seed Leave Records
                leave_count = 4 if p["heavy_leaves"] else 1
                for l_idx in range(leave_count):
                    start = today - timedelta(days=(l_idx + 1) * 20)
                    days = 3 if p["heavy_leaves"] else 1
                    lv = Leave(
                        employee_id=emp.id,
                        leave_type=LeaveTypeEnum.SICK if p["heavy_leaves"] else LeaveTypeEnum.CASUAL,
                        start_date=start,
                        end_date=start + timedelta(days=days - 1),
                        total_days=days,
                        reason="Scheduled or medical leave",
                        status=LeaveStatusEnum.APPROVED
                    )
                    db.add(lv)

                db.commit()

        print("Database seeding completed successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
