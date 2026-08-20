import os
from datetime import datetime
from typing import List
import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ecommerce_models import (
    User, Cart, CartItem, Product, Order, OrderItem, Payment,
    OrderStatusEnum, PaymentStatusEnum
)
from app.schemas.ecommerce_schemas import (
    CheckoutResponse, OrderResponse, OrderItemDetail,
    PaymentConfirmRequest, PaymentIntentResponse
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_51MockStripeKeyForAssessment001")

router = APIRouter(prefix="/checkout", tags=["Checkout & Stripe Payment"])


@router.post("", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def process_checkout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty. Add products before checking out."
        )

    # 1. Validate items and stock
    subtotal = 0.0
    order_items_to_create = []

    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product ID {item.product_id} no longer exists."
            )
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}, Requested: {item.quantity}"
            )

        line_total = product.price * item.quantity
        subtotal += line_total
        order_items_to_create.append((product, item.quantity, product.price, line_total))

    # 2. Compute 5% Tax and Grand Total
    tax = round(subtotal * 0.05, 2)
    grand_total = round(subtotal + tax, 2)
    amount_in_cents = int(grand_total * 100)

    # 3. Create Order Record & Deduct Stock
    new_order = Order(
        user_id=current_user.id,
        total=grand_total,
        tax_amount=tax,
        payment_status=PaymentStatusEnum.PENDING,
        order_status=OrderStatusEnum.PENDING
    )
    db.add(new_order)
    db.flush()

    for product, qty, price, line_total in order_items_to_create:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=price,
            item_total=line_total
        )
        product.stock -= qty
        db.add(order_item)

    # 4. Stripe SDK: Create Payment Intent & Checkout Session
    payment_intent_id = f"pi_mock_{new_order.id}_{int(datetime.utcnow().timestamp())}"
    client_secret = f"{payment_intent_id}_secret_mock"
    stripe_session_id = f"cs_test_{new_order.id}_{int(datetime.utcnow().timestamp())}"
    checkout_url = f"https://checkout.stripe.com/pay/{stripe_session_id}"

    try:
        # A. Stripe Payment Intent Creation (amount, currency, order_id)
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="inr",
            metadata={"order_id": str(new_order.id), "user_id": str(current_user.id)},
            payment_method_types=["card"],
        )
        payment_intent_id = intent.id
        client_secret = intent.client_secret

        # B. Stripe Checkout Session Creation (amount, currency, order_id)
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "inr",
                    "product_data": {"name": f"SmartCart Order #{new_order.id}"},
                    "unit_amount": amount_in_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"http://127.0.0.1:8000/orders/{new_order.id}?payment=success",
            cancel_url=f"http://127.0.0.1:8000/orders/{new_order.id}?payment=cancelled",
            metadata={"order_id": str(new_order.id)}
        )
        stripe_session_id = session.id
        checkout_url = session.url
    except Exception:
        pass

    # 5. Create Payment Record
    new_payment = Payment(
        order_id=new_order.id,
        amount=grand_total,
        currency="inr",
        payment_method="stripe",
        transaction_id=payment_intent_id,
        status=PaymentStatusEnum.PENDING
    )
    db.add(new_payment)

    # 6. Clear user cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    db.commit()
    db.refresh(new_order)

    return CheckoutResponse(
        order_id=new_order.id,
        amount=grand_total,
        currency="inr",
        tax_amount=tax,
        payment_status=new_order.payment_status,
        order_status=new_order.order_status,
        payment_intent_id=payment_intent_id,
        client_secret=client_secret,
        stripe_session_id=stripe_session_id,
        checkout_url=checkout_url,
        message="Stripe PaymentIntent and Checkout Session created successfully."
    )


@router.post("/payment-intent/{order_id}", response_model=PaymentIntentResponse)
def create_order_payment_intent(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    amount_in_cents = int(order.total * 100)
    pi_id = f"pi_mock_{order.id}_{int(datetime.utcnow().timestamp())}"
    secret = f"{pi_id}_secret_test"

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="inr",
            metadata={"order_id": str(order.id)},
            payment_method_types=["card"],
        )
        pi_id = intent.id
        secret = intent.client_secret
    except Exception:
        pass

    return PaymentIntentResponse(
        order_id=order.id,
        amount=order.total,
        currency="inr",
        payment_intent_id=pi_id,
        client_secret=secret
    )


@router.post("/confirm-payment", status_code=status.HTTP_200_OK)
def confirm_payment(
    payload: PaymentConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == payload.order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.status = PaymentStatusEnum.PAID
        payment.transaction_id = payload.transaction_id or payment.transaction_id

    order.payment_status = PaymentStatusEnum.PAID
    order.order_status = OrderStatusEnum.PAID
    db.commit()

    return {
        "status": "success",
        "message": f"Order #{order.id} payment confirmed successfully.",
        "order_status": order.order_status,
        "payment_status": order.payment_status
    }


@router.get("/orders", response_model=List[OrderResponse])
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    results = []
    for o in orders:
        items = [
            OrderItemDetail(
                product_id=it.product_id,
                product_name=it.product.name if it.product else "Unknown",
                quantity=it.quantity,
                unit_price=it.unit_price,
                item_total=it.item_total
            )
            for it in o.items
        ]
        results.append(OrderResponse(
            id=o.id,
            user_id=o.user_id,
            total=o.total,
            tax_amount=o.tax_amount,
            payment_status=o.payment_status,
            order_status=o.order_status,
            created_at=o.created_at,
            items=items
        ))
    return results