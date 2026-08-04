from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from models.job import Job, JobStatus
from core.schemas import JobCreate, JobResponse
from core.tasks import process_job_task

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# 1. Submit a new job
@router.post("/", response_model=JobResponse)
def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    new_job = Job(
        task_type=job_data.task_type,
        payload=job_data.payload,
        priority=job_data.priority,
        max_retries=job_data.max_retries,
        status=JobStatus.PENDING
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    process_job_task.delay(new_job.id)
    return new_job

# 2. Get all jobs
@router.get("/", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()

# 3. Get job details by ID
@router.get("/{job_id}", response_model=JobResponse)
def get_job_by_id(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# 4. Job Statistics / Monitoring Dashboard metrics
@router.get("/metrics/dashboard")
def get_metrics(db: Session = Depends(get_db)):
    total = db.query(Job).count()
    pending = db.query(Job).filter(Job.status == JobStatus.PENDING).count()
    running = db.query(Job).filter(Job.status == JobStatus.RUNNING).count()
    completed = db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
    failed = db.query(Job).filter(Job.status == JobStatus.FAILED).count()
    
    return {
        "total_jobs": total,
        "pending_jobs": pending,
        "running_jobs": running,
        "completed_jobs": completed,
        "failed_jobs": failed
    }