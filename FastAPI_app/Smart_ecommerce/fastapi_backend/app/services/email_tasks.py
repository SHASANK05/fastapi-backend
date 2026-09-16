import time
try:
    from app.core.celery_app import celery_app
except (ImportError, ModuleNotFoundError):
    from core.celery_app import celery_app

@celery_app.task(name="send_order_confirmation_email")
def send_order_confirmation_email(user_email: str, order_id: int, total_amount: float):
    """Simulates sending an asynchronous confirmation email."""
    print(f"--> [Celery Worker] Starting email dispatch to {user_email} for Order #{order_id}...")
    time.sleep(2)  # Simulate network latency of sending an email
    print(f"--> [Celery Worker] Confirmation email sent successfully to {user_email}!")
    return {"status": "sent", "order_id": order_id, "recipient": user_email}

@celery_app.task(name="send_return_status_email")
def send_return_status_email(user_email: str, order_id: int, status: str):
    """Simulates sending a return approval/rejection update."""
    print(f"--> [Celery Worker] Sending return update ({status}) to {user_email} for Order #{order_id}...")
    time.sleep(1)
    return {"status": "sent", "order_id": order_id, "update": status}