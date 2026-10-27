import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Employee, RiskCategoryEnum
from app.api.v1.predictions import evaluate_single_employee

logger = logging.getLogger("workforce_scheduler")
logging.basicConfig(level=logging.INFO)

scheduler = AsyncIOScheduler()

def run_nightly_attrition_recalculation():
    """
    Background job: Scans all active employees, calculates latest
    attendance/leave/compensation metrics, runs the ML engine,
    and saves new prediction records.
    """
    logger.info(f"[{datetime.now()}] Starting scheduled bulk attrition recalculation...")
    db: Session = SessionLocal()
    try:
        employees = db.query(Employee).filter(Employee.is_active == True).all()
        if not employees:
            logger.info("No active employees found. Skipping scheduled run.")
            return

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
        logger.info(
            f"Scheduled run complete: {len(employees)} scored | "
            f"High: {high_cnt}, Moderate: {mod_cnt}, Low: {low_cnt}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during scheduled attrition calculation: {str(e)}", exc_info=True)
    finally:
        db.close()

def start_scheduler():
    """
    Initializes and starts the background task runner.
    Default schedule: Nightly at 00:00 (midnight).
    """
    if not scheduler.running:
        scheduler.add_job(
            run_nightly_attrition_recalculation,
            trigger=CronTrigger(hour=0, minute=0),
            id="nightly_attrition_job",
            name="Nightly Workforce Attrition Evaluation",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler initialized and active.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler shutdown successfully.")
