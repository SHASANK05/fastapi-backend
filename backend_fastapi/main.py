import uuid
from datetime import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from fraud_engine import evaluate_transaction_risk

from database import engine, get_db, Base
import models
import schemas
from auth import get_current_user_id
from auth import get_current_user, require_roles
from auth import require_roles
from auth import get_current_user, get_current_user_id, require_roles

# Create payment_transactions table automatically if not present
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Credit Card Payment Gateway API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/admin/health-check")
def admin_only_check(user: dict = Depends(require_roles("ADMIN"))):
    return {"status": "ok", "message": f"Welcome Admin {user.get('username')}"}

@app.post("/api/payments/process/", response_model=schemas.PaymentResponse)
def process_payment(
    payload: schemas.PaymentRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # Verify card exists and belongs to the authenticated user
    card = db.query(models.Card).filter(
        models.Card.id == payload.card_id,
        models.Card.user_id == user_id
    ).first()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found or does not belong to the user"
        )

    # Run through Fraud Engine
    risk_assessment = evaluate_transaction_risk(
        db=db,
        card_id=card.id,
        user_id=user_id,
        amount=payload.amount,
        cvv=payload.cvv,
    )

    is_success = risk_assessment.is_allowed
    failure_reason = risk_assessment.reason
    txn_status = risk_assessment.status

    txn = models.Transaction(
        user_id=user_id,
        card_id=card.id,
        merchant_name=payload.merchant_name,
        amount=payload.amount,
        currency="INR",
        status="SUCCESS" if is_success else "FAILED",
        failure_reason=failure_reason,
        transaction_reference=f"TXN-{uuid.uuid4().hex[:12].upper()}"
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    return schemas.PaymentResponse(
        transaction_id=txn.id,
        reference_id=txn.transaction_reference,
        merchant=txn.merchant_name,
        amount=txn.amount,
        currency=txn.currency,
        status=txn.status,
        failure_reason=txn.failure_reason,
        created_at=txn.created_at
    )


@app.get("/api/payments/transactions/", response_model=List[schemas.PaymentResponse])
def get_user_transactions(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id
    ).order_by(models.Transaction.created_at.desc()).all()

    return [
        schemas.PaymentResponse(
            transaction_id=t.id,
            reference_id=t.transaction_reference,
            merchant=t.merchant_name,
            amount=t.amount,
            currency=t.currency,
            status=t.status,
            failure_reason=t.failure_reason,
            created_at=t.created_at
        ) for t in transactions
    ]


@app.get("/dashboard/summary", response_model=schemas.DashboardSummaryResponse)
def get_dashboard_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identification"
        )

    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # 1. Total Transactions Count
    total_tx_count = db.query(func.count(models.Transaction.id))\
        .filter(models.Transaction.user_id == uid)\
        .scalar() or 0

    # 2. Total Amount Spent (SUCCESS only)
    total_spent = db.query(func.coalesce(func.sum(models.Transaction.amount), 0.0))\
        .filter(
            models.Transaction.user_id == uid,
            models.Transaction.status == "SUCCESS"
        ).scalar() or 0.0

    # 3. Current Month Spending
    month_spent = db.query(func.coalesce(func.sum(models.Transaction.amount), 0.0))\
        .filter(
            models.Transaction.user_id == uid,
            models.Transaction.status == "SUCCESS",
            extract('year', models.Transaction.created_at) == current_year,
            extract('month', models.Transaction.created_at) == current_month
        ).scalar() or 0.0

    # 4. Available Credit Limit (₹1,00,000 per card)
    card_count = db.query(func.count(models.Card.id))\
        .filter(models.Card.user_id == uid)\
        .scalar() or 0
    total_limit = float(max(1, card_count) * 100000.0)
    available_limit = max(0.0, total_limit - float(total_spent))

    # 5. Last 5 Transactions
    transactions = db.query(models.Transaction)\
        .filter(models.Transaction.user_id == uid)\
        .order_by(desc(models.Transaction.created_at))\
        .limit(5)\
        .all()

    last_5 = []
    for tx in transactions:
        card = db.query(models.Card).filter(models.Card.id == tx.card_id).first()
        
        # Safely extract masked card string regardless of exact model field name
        masked_val = "•••• •••• •••• 4444"
        if card:
            masked_val = (
                getattr(card, 'masked_number', None) or 
                getattr(card, 'card_masked', None) or 
                getattr(card, 'card_number', None) or 
                (f"•••• •••• •••• {getattr(card, 'last_four', '4444')}")
            )

        last_5.append(
            schemas.RecentTransaction(
                id=tx.id,
                amount=float(tx.amount),
                masked_card_number=str(masked_val),
                date=tx.created_at,
                status=tx.status,
                merchant_name=tx.merchant_name or "Online Merchant"
            )
        )

    return schemas.DashboardSummaryResponse(
        total_transactions=int(total_tx_count),
        total_amount_spent=round(float(total_spent), 2),
        current_month_spending=round(float(month_spent), 2),
        available_credit_limit=round(float(available_limit), 2),
        last_5_transactions=last_5
    )

@app.get(
    "/api/admin/transactions/flagged/",
    response_model=schemas.FlaggedTransactionsResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
)
def get_flagged_transactions(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Retrieve all flagged or failed transactions for administrative review."""
    query = (
        db.query(models.Transaction)
        .filter(models.Transaction.status.in_(["FAILED", "FLAGGED_FRAUD"]))
        .order_by(models.Transaction.created_at.desc())
    )
    total = query.count()
    records = query.offset(offset).limit(limit).all()

    return {
        "total_count": total,
        "transactions": records
    }


@app.post(
    "/api/admin/transactions/{transaction_id}/review/",
    dependencies=[Depends(require_roles("ADMIN"))],
)
def review_transaction(
    transaction_id: int,
    payload: schemas.ReviewTransactionRequest,
    current_admin: dict = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    """Allows an administrator to mark a suspicious transaction as reviewed."""
    txn = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if payload.action not in ["RESOLVED", "CONFIRMED_FRAUD"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid action. Must be 'RESOLVED' or 'CONFIRMED_FRAUD'"
        )

    admin_username = current_admin.get("username", "admin")
    txn.status = payload.action
    txn.failure_reason = f"[{payload.action} by {admin_username}] Note: {payload.notes or 'None'}"

    db.commit()
    db.refresh(txn)

    return {
        "status": "success",
        "transaction_id": txn.id,
        "new_status": txn.status,
        "reviewed_by": admin_username,
        "audit_note": txn.failure_reason
    }