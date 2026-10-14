"""
Standalone Database Seeder for HRMS
Initializes tables and seeds baseline admin, departments, employee, and payroll.
"""
from datetime import date
from app.database import engine, SessionLocal, Base
from app.models import (
    User, Employee, Department, RoleEnum,
    LeaveType, LeaveBalance, Payroll
)
import app.security as security

# Resolve the password hashing function regardless of naming
if hasattr(security, "get_password_hash"):
    hash_fn = security.get_password_hash
elif hasattr(security, "hash_password"):
    hash_fn = security.hash_password
elif hasattr(security, "pwd_context"):
    hash_fn = security.pwd_context.hash
else:
    # Direct fallback using passlib CryptContext
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash_fn = pwd_context.hash

def seed_database():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Admin Account
        admin = db.query(User).filter(User.email == "admin@hrms.com").first()
        if not admin:
            admin = User(
                email="admin@hrms.com",
                hashed_password=hash_fn("Admin@12345"),
                role=RoleEnum.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("✔ Admin user created: admin@hrms.com")
        else:
            print("✔ Admin user already exists")

        # 2. Departments
        eng_dept = db.query(Department).filter(Department.name == "Engineering").first()
        if not eng_dept:
            eng_dept = Department(name="Engineering", description="Core Platform Engineering")
            db.add(eng_dept)
            db.commit()
            db.refresh(eng_dept)
            print("✔ Engineering Department created")
        else:
            print("✔ Engineering Department already exists")

        # 3. Employee Account (Siva)
        emp_user = db.query(User).filter(User.email == "siva@hrms.com").first()
        if not emp_user:
            emp_user = User(
                email="siva@hrms.com",
                hashed_password=hash_fn("Password@123"),
                role=RoleEnum.EMPLOYEE,
                is_active=True
            )
            db.add(emp_user)
            db.commit()
            db.refresh(emp_user)

            emp_profile = Employee(
                user_id=emp_user.id,
                emp_code="EMP-101",
                first_name="Siva",
                last_name="Kumar",
                email="siva@hrms.com",
                phone="9876543210",
                department_id=eng_dept.id,
                designation="Software Engineer",
                joining_date=date(2024, 1, 15)
            )
            db.add(emp_profile)
            db.commit()
            db.refresh(emp_profile)
            print("✔ Employee created: siva@hrms.com (EMP-101)")

            # 4. Leave Types & Balance
            annual_leave = LeaveType(name="Annual Leave", default_days_per_year=18)
            sick_leave = LeaveType(name="Sick Leave", default_days_per_year=12)
            db.add_all([annual_leave, sick_leave])
            db.commit()

            bal = LeaveBalance(
                employee_id=emp_profile.id,
                leave_type_id=annual_leave.id,
                year=2026,
                allocated_days=18,
                used_days=0
            )
            db.add(bal)
            db.commit()

            # 5. October 2026 Seed Payroll
            pay = Payroll(
                employee_id=emp_profile.id,
                month=10,
                year=2026,
                base_salary=60000.0,
                allowances=10000.0,
                deductions=2000.0,
                lop_days=0,
                lop_amount=0.0,
                net_salary=68000.0,
                is_locked=True
            )
            db.add(pay)
            db.commit()
            print("✔ Sample October 2026 Payroll seeded (₹68,000)")
        else:
            print("✔ Employee user already exists")

        print("\nAll database tables and seed records are up-to-date!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
