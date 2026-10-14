import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("hrms_notifications")
logger.setLevel(logging.INFO)


class NotificationService:
    @staticmethod
    def send_email(to_email: str, subject: str, template_body: str) -> bool:
        """
        Simulates enterprise email dispatch and logs formatted templates.
        Ready for SMTP / SendGrid / SES integration.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "=" * 60)
        print(f"📧 [EMAIL DISPATCHED] at {timestamp}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(template_body)
        print("=" * 60 + "\n")
        return True

    @classmethod
    def notify_employee_onboarding(cls, emp_email: str, emp_name: str, emp_code: str):
        subject = f"Welcome to the Organization - Employee ID: {emp_code}"
        body = (
            f"Dear {emp_name},\n\n"
            f"Welcome aboard! Your employee profile has been created with Code: {emp_code}.\n"
            f"You can now log in to the HRMS portal to view your dashboard, mark attendance, and submit leave requests.\n\n"
            f"Best regards,\nHR Operations Team"
        )
        return cls.send_email(emp_email, subject, body)

    @classmethod
    def notify_leave_status(cls, emp_email: str, emp_name: str, leave_type: str, status: str, approver_comment: Optional[str] = None):
        subject = f"Leave Request Update: {status.upper()}"
        body = (
            f"Dear {emp_name},\n\n"
            f"Your request for {leave_type} has been {status.upper()}.\n"
        )
        if approver_comment:
            body += f"Notes: {approver_comment}\n"
        body += "\nPlease check your HRMS portal for your updated balance.\n\nBest regards,\nHR Operations Team"
        return cls.send_email(emp_email, subject, body)

    @classmethod
    def notify_payroll_generated(cls, emp_email: str, emp_name: str, month: int, year: int, net_salary: float):
        subject = f"Payslip Available for {month:02d}/{year}"
        body = (
            f"Dear {emp_name},\n\n"
            f"Your salary slip for {month:02d}/{year} has been processed.\n"
            f"Net Disbursed Salary: ₹{net_salary:,.2f}\n\n"
            f"You can log in to your employee portal to download your official PDF payslip.\n\n"
            f"Best regards,\nPayroll Team"
        )
        return cls.send_email(emp_email, subject, body)