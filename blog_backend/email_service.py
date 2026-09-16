import logging

logger = logging.getLogger("uvicorn")

def send_notification_email(recipient_email: str, subject: str, body: str):
    logger.info(f"\n[EMAIL DISPATCH] --------------------")
    logger.info(f"To: {recipient_email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body: {body}")
    logger.info(f"-------------------------------------\n")