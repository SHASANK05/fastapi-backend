from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.job import JobStatus

class JobCreate(BaseModel):
    task_type: str
    payload: Optional[str] = None
    priority: Optional[int] = 1
    max_retries: Optional[int] = 3

class JobResponse(BaseModel):
    id: str
    task_type: str
    payload: Optional[str] = None
    status: JobStatus
    priority: int
    retries: int
    max_retries: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True