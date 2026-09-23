import os
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import get_db
from models import User, SubscriptionPlan, BillingHistory, PlanType, Notification
from security import get_current_user
from invoice_service import generate_invoice_pdf

router = APIRouter(prefix="/subscription", tags=["Subscription & Billing"])

class PlanUpgradeRequest(BaseModel):
    plan_name: PlanType

@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_to_plan(
    req: PlanUpgradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)

    # Upsert active subscription
    sub = db.query(SubscriptionPlan).filter(SubscriptionPlan.user_id == current_user.id).first()
    if sub:
        sub.plan_name = req.plan_name
        sub.start_date = start_date
        sub.end_date = end_date
        sub.is_active = 1
    else:
        sub = SubscriptionPlan(
            user_id=current_user.id,
            plan_name=req.plan_name,
            start_date=start_date,
            end_date=end_date,
            is_active=1
        )
        db.add(sub)

    # Generate invoice PDF
    invoice_path, tx_id, price = generate_invoice_pdf(
        user_name=current_user.username,
        plan_name=req.plan_name.value,
        start_date=start_date,
        end_date=end_date
    )

    # Save to BillingHistory
    billing = BillingHistory(
        user_id=current_user.id,
        plan_name=req.plan_name.value,
        price=price,
        transaction_id=tx_id,
        invoice_path=invoice_path
    )
    db.add(billing)

    # Trigger In-App Notification
    sub_notif = Notification(
        recipient_id=current_user.id,
        actor_id=None,
        notification_type="subscription",
        message=f"Your subscription has been updated to the {req.plan_name.value.capitalize()} plan!"
    )
    db.add(sub_notif)

    # Commit all changes atomically
    db.commit()

    filename = os.path.basename(invoice_path)
    return {
        "message": f"Successfully subscribed to {req.plan_name.value} plan!",
        "transaction_id": tx_id,
        "price_paid": price,
        "invoice_download_url": f"/media/invoices/{filename}"
    }

@router.get("/history")
def get_billing_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(BillingHistory).filter(BillingHistory.user_id == current_user.id).all()