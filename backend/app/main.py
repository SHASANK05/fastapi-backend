from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
import app.models.models
from app.api.v1 import auth, departments, employees, attendance, leaves, predictions, audit, retention, datasets
from app.services.scheduler import start_scheduler, stop_scheduler

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title="WorkForce AI Pro",
    version="1.0.0",
    description="HR Attrition Prediction & Workforce Intelligence System",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(leaves.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(retention.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "system": "WorkForce AI Pro",
        "status": "operational",
        "docs": "/docs"
    }
