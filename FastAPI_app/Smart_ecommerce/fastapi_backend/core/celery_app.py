import os
from celery import Celery

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Support both flat and nested package imports
try:
    import services.email_tasks
    task_modules = ["services.email_tasks"]
except ImportError:
    task_modules = ["app.services.email_tasks"]

celery_app = Celery(
    "ecommerce_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=task_modules,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)