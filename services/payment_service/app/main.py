import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Payment, PaymentStatus
from app.schemas import PaymentProcessRequest, PaymentResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="ShopEase Payment & Transaction Service", version="1.0.0", lifespan=lifespan)

@app.get("/")
def root():
    return {"service": "Payment Service", "status": "operational", "port": 8005}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/payments/process", response_model=PaymentResponse)
def process_payment(payload: PaymentProcessRequest, db: Session = Depends(get_db)):
    if payload.simulate_failure:
        failed_record = Payment(
            order_id=payload.order_id,
            amount=payload.amount,
            status=PaymentStatus.FAILED,
            payment_method=payload.payment_method,
            transaction_ref=None
        )
        db.add(failed_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment transaction declined or insufficient balance"
        )

    tx_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    payment = Payment(
        order_id=payload.order_id,
        amount=payload.amount,
        status=PaymentStatus.SUCCESS,
        payment_method=payload.payment_method,
        transaction_ref=tx_ref
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@app.get("/api/v1/payments/order/{order_id}", response_model=PaymentResponse)
def get_payment_by_order(order_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")
    return payment
