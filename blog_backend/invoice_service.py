import os
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

INVOICE_DIR = os.path.join("media", "invoices")
os.makedirs(INVOICE_DIR, exist_ok=True)

# Pricing in Indian Rupees (INR)
PLAN_PRICES = {
    "Basic": 0.00,
    "Premium": 499.00,
    "Pro": 1499.00
}

def generate_invoice_pdf(user_name: str, plan_name: str, start_date: datetime, end_date: datetime) -> tuple[str, str, float]:
    tx_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
    filename = f"invoice_{tx_id}.pdf"
    file_path = os.path.join(INVOICE_DIR, filename)
    price = PLAN_PRICES.get(plan_name, 0.00)

    # Generate PDF using ReportLab
    c = canvas.Canvas(file_path, pagesize=letter)
    
    # Document Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 740, "Blog Platform - Subscription Invoice")
    c.line(50, 725, 550, 725)

    # Invoice Metadata
    c.setFont("Helvetica", 11)
    c.drawString(50, 680, f"Transaction ID : {tx_id}")
    c.drawString(50, 655, f"Issued Date    : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, 630, f"Customer Name  : {user_name}")
    c.drawString(50, 605, f"Plan Name      : {plan_name}")
    c.drawString(50, 580, f"Period         : {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Payment Summary in INR
    c.line(50, 560, 550, 560)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 535, f"Total Paid     : Rs. {price:,.2f} (INR)")

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 490, "Generated automatically by Blog Management Billing System.")

    c.save()
    return file_path, tx_id, price