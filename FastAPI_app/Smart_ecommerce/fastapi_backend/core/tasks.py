import time
from datetime import datetime
from core.celery_app import celery_app
from core.database import SessionLocal
from models.job import Job, JobStatus

@celery_app.task(bind=True)
def process_job_task(self, job_id: str):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        db.close()
        return

    try:
        # Mark status as Running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        # Simulate task work (e.g. 5 seconds execution)
        time.sleep(5)

        # Mark status as Completed
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as exc:
        job.retries += 1
        job.error_message = str(exc)

        if job.retries < job.max_retries:
            job.status = JobStatus.PENDING
            db.commit()
            db.close()
            # Retry automatically
            raise self.retry(exc=exc, countdown=2 ** job.retries)
        else:
            job.status = JobStatus.FAILED
            db.commit()
            db.close()
            raise exc
    finally:
        db.close()