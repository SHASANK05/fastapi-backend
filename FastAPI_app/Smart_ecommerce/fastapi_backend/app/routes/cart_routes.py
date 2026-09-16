from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
except (ImportError, ModuleNotFoundError):
    from core.database import get_db

try:
    from core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from app.core.security import get_current_user
    
try:
    from app.models.ecommerce_models import (
        User,
        Product,
        Cart,
        CartItem,
        Order,
        OrderItem,
        Payment,
        OrderStatusEnum,
        PaymentStatusEnum,
        NotificationTypeEnum,
    )
except (ImportError, ModuleNotFoundError):
    from models.ecommerce_models import (
        User,
        Product,
        Cart,
        CartItem,
        Order,
        OrderItem,
        Payment,
        OrderStatusEnum,
        PaymentStatusEnum,
        NotificationTypeEnum,
    )

try:
    from app.services.admin_return_service import create_notification
except (ImportError, ModuleNotFoundError):
    from services.admin_return_service import create_notification

try:
    from app.services.email_tasks import send_order_confirmation_email
except (ImportError, ModuleNotFoundError):
    from services.email_tasks import send_order_confirmation_email

router = APIRouter(prefix="/cart", tags=["Cart & Checkout"])


class AddToCartSchema(BaseModel):
    product_id: int
    quantity: int = Field(default=1, gt=0)


class UpdateCartItemSchema(BaseModel):
    quantity: int = Field(..., gt=0)


def _get_or_create_user_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id, created_at=datetime.utcnow())
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


# 1. GET /cart - Fetch current user's cart with items and total calculation
@router.get("")
def view_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = _get_or_create_user_cart(db, current_user.id)
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()

    cart_summary = []
    subtotal = 0.0

    for item in items:
        prod = (
            db.query(Product).filter(Product.id == item.product_id).first()
        )
        if prod:
            item_total = round(prod.price * item.quantity, 2)
            subtotal += item_total
            cart_summary.append(
                {
                    "item_id": item.id,
                    "product_id": prod.id,
                    "name": prod.name,
                    "unit_price": prod.price,
                    "quantity": item.quantity,
                    "available_stock": prod.stock,
                    "item_total": item_total,
                }
            )

    tax = round(subtotal * 0.05, 2)
    grand_total = round(subtotal + tax, 2)

    return {
        "cart_id": cart.id,
        "items": cart_summary,
        "subtotal": subtotal,
        "tax": tax,
        "grand_total": grand_total,
    }


# 2. POST /cart/items - Add product to cart with stock validation
@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_to_cart(
    payload: AddToCartSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = (
        db.query(Product).filter(Product.id == payload.product_id).first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    if product.stock < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient inventory. Only {product.stock} units available.",
        )

    cart = _get_or_create_user_cart(db, current_user.id)
    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == payload.product_id,
        )
        .first()
    )

    if cart_item:
        new_quantity = cart_item.quantity + payload.quantity
        if product.stock < new_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot add {payload.quantity} more. Exceeds available stock of {product.stock}.",
            )
        cart_item.quantity = new_quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        db.add(cart_item)

    db.commit()
    return {"message": "Product added to cart", "cart_id": cart.id}


# 3. PUT /cart/items/{item_id} - Update item quantity
@router.put("/items/{item_id}")
def update_cart_item(
    item_id: int,
    payload: UpdateCartItemSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = _get_or_create_user_cart(db, current_user.id)
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if not cart_item:
        raise HTTPException(
            status_code=404, detail="Cart line item not found."
        )

    product = (
        db.query(Product).filter(Product.id == cart_item.product_id).first()
    )
    if product and product.stock < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insufficient. Max available is {product.stock}.",
        )

    cart_item.quantity = payload.quantity
    db.commit()
    return {"message": "Cart item updated", "quantity": cart_item.quantity}


# 4. DELETE /cart/items/{item_id} - Remove single item
@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = _get_or_create_user_cart(db, current_user.id)
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    db.delete(cart_item)
    db.commit()
    return None


# 5. POST /cart/checkout - Convert cart to order, deduct stock, record payment, dispatch Celery task
@router.post("/checkout")
def checkout_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = _get_or_create_user_cart(db, current_user.id)
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()

    if not items:
        raise HTTPException(
            status_code=400,
            detail="Your cart is empty. Add items before checking out.",
        )

    # 1. Validate inventory availability across all items
    for item in items:
        prod = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .with_for_update()
            .first()
        )
        if not prod or prod.stock < item.quantity:
            available = prod.stock if prod else 0
            raise HTTPException(
                status_code=400,
                detail=f"Checkout blocked: '{prod.name if prod else 'Item'}' only has {available} in stock.",
            )

    # 2. Calculate subtotal, tax, and grand total
    subtotal = 0.0
    for item in items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        subtotal += prod.price * item.quantity

    tax_amount = round(subtotal * 0.05, 2)
    grand_total = round(subtotal + tax_amount, 2)

    # 3. Create Order
    new_order = Order(
        user_id=current_user.id,
        total=grand_total,
        tax_amount=tax_amount,
        payment_status=PaymentStatusEnum.PAID,
        order_status=OrderStatusEnum.PAID,
        created_at=datetime.utcnow(),
    )
    db.add(new_order)
    db.flush()  # Populates new_order.id

    order_id = new_order.id
    order_status_val = (
        new_order.order_status.value
        if hasattr(new_order.order_status, "value")
        else str(new_order.order_status)
    )
    payment_status_val = (
        new_order.payment_status.value
        if hasattr(new_order.payment_status, "value")
        else str(new_order.payment_status)
    )

    # 4. Create OrderItems & Deduct Stock
    for item in items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        item_total = round(prod.price * item.quantity, 2)

        order_item = OrderItem(
            order_id=order_id,
            product_id=prod.id,
            quantity=item.quantity,
            unit_price=prod.price,
            item_total=item_total,
        )
        db.add(order_item)
        prod.stock -= item.quantity

    # 5. Record Payment
    payment_record = Payment(
        order_id=order_id,
        amount=grand_total,
        currency="inr",
        payment_method="mock_gateway",
        transaction_id=f"txn_{int(datetime.utcnow().timestamp())}",
        status=PaymentStatusEnum.PAID,
        timestamp=datetime.utcnow(),
    )
    db.add(payment_record)

    # 6. Empty Cart
    for item in items:
        db.delete(item)

    # 7. Commit primary transaction
    db.commit()

    # 8. Create Notification safely
    try:
        create_notification(
            db,
            user_id=current_user.id,
            notif_type=NotificationTypeEnum.ORDER_CONFIRMED,
            message=f"Order #{order_id} confirmed! Total paid: ₹{grand_total}",
        )
    except Exception:
        pass

    # 9. Asynchronously dispatch Celery background email task
    try:
        send_order_confirmation_email.delay(
            user_email=current_user.email,
            order_id=order_id,
            total_amount=grand_total,
        )
    except Exception as e:
        print(f"[Celery] Background dispatch error: {e}")

    return {
        "message": "Checkout completed successfully! Order placed.",
        "order_id": order_id,
        "grand_total": grand_total,
        "order_status": order_status_val,
        "payment_status": payment_status_val,
    }