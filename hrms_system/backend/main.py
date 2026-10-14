from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, SessionLocal
from app.models import User, RoleEnum
from app.security import hash_password
from app.routers import auth, employees, attendance
from app.routers import auth, employees, attendance, leaves
from app.routers import auth, employees, attendance, leaves, payroll
from app.routers import auth, employees, attendance, leaves, payroll, dashboard
from app.routers import auth, employees, attendance, leaves, payroll, dashboard, reports
from app.routers import auth, employees, attendance, leaves, payroll, dashboard, reports, audit

# Auto-create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HRMS Core API",
    description="Enterprise HRMS with RBAC, Attendance, Leave, and Payroll",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leaves.router)
app.include_router(payroll.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(audit.router)


@app.on_event("startup")
def create_initial_admin():
    db = SessionLocal()
    admin_email = "admin@hrms.com"
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if not existing_admin:
        admin_user = User(
            email=admin_email,
            hashed_password=hash_password("Admin@12345"),
            role=RoleEnum.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
    db.close()


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "HRMS Backend"}


@app.get("/")
def root():
    return {
        "message": "HRMS API is running",
        "docs": "/docs",
        "health": "/health"
    }