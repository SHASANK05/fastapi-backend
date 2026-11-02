import os
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Order, OrderStatus
from app.schemas import OrderCreateRequest, OrderResponse

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product_service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:8000")

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="ShopEase Order Orchestrator Service", version="1.0.0", lifespan=lifespan)

@app.get("/")
def root():
    return {"service": "Order Service", "status": "operational", "port": 8004}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest, 
    x_user_id: int = Header(default=1), 
    db: Session = Depends(get_db)
):
    # Step 1: Initialize local pending order
    order = Order(
        user_id=x_user_id,
        sku=payload.sku,
        quantity=payload.quantity,
        total_amount=payload.total_amount,
        status=OrderStatus.PENDING
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 2: Reserve Stock in Product Service
        reserve_res = await client.post(
            f"{PRODUCT_SERVICE_URL}/api/v1/products/reserve",
            json={"sku": payload.sku, "quantity": payload.quantity}
        )

        if reserve_res.status_code != 200:
            order.status = OrderStatus.CANCELLED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Stock reservation failed: {reserve_res.text}"
            )

        # Step 3: Process Payment in Payment Service
        payment_payload = {
            "order_id": order.id,
            "amount": payload.total_amount,
            "payment_method": "UPI",
            "simulate_failure": payload.simulate_payment_failure
        }
        pay_res = await client.post(
            f"{PAYMENT_SERVICE_URL}/api/v1/payments/process",
            json=payment_payload
        )

        # Step 4: Handle Failure -> Compensating Action (Release Stock)
        if pay_res.status_code != 200:
            await client.post(
                f"{PRODUCT_SERVICE_URL}/api/v1/products/release",
                json={"sku": payload.sku, "quantity": payload.quantity}
            )
            order.status = OrderStatus.FAILED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Payment declined. Compensating transaction executed: inventory released."
            )

        # Step 5: Saga Succeeded -> Finalize Order as PAID
        order.status = OrderStatus.PAID
        db.commit()
        db.refresh(order)
        return order

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
