import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db, Base
import models
import schemas
from auth import get_current_user_id

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

    # Simulation logic:
    # 1. CVV '000' triggers simulated bank authorization failure
    # 2. Transaction amounts above ₹50,000 trigger simulated limit failure
    is_success = True
    failure_reason = None

    if payload.cvv == "000":
        is_success = False
        failure_reason = "Payment rejected: Invalid CVV / Bank authorization failed."
    elif payload.amount > 50000:
        is_success = False
        failure_reason = "Transaction limit exceeded: Max transaction limit is ₹50,000."

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