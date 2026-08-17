from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.models.ecommerce_models import User, Product, Cart, CartItem
from app.schemas.ecommerce_schemas import (
    CartItemAdd,
    CartItemUpdate,
    CartItemRemove,
    CartResponse,
    CartItemResponse
)
from app.routes.auth_routes import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart Management"])

TAX_RATE = 0.05  # 5% Tax rate


# --- Helper: Get or create single cart per user ---
def get_or_create_user_cart(user_id: int, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


# --- Helper: Calculate Item Total, Cart Total, Tax & Grand Total ---
def calculate_cart_details(cart: Cart) -> CartResponse:
    items_response = []
    cart_total = 0.0

    for item in cart.items:
        product = item.product
        item_total = round(product.price * item.quantity, 2)
        cart_total += item_total
        items_response.append(
            CartItemResponse(
                product_id=product.id,
                name=product.name,
                unit_price=product.price,
                quantity=item.quantity,
                item_total=item_total
            )
        )

    tax_amount = round(cart_total * TAX_RATE, 2)
    grand_total = round(cart_total + tax_amount, 2)

    return CartResponse(
        cart_id=cart.id,
        user_id=cart.user_id,
        items=items_response,
        cart_total=round(cart_total, 2),
        tax_amount=tax_amount,
        grand_total=grand_total
    )


# 1. GET /cart (View user's cart with full calculation)
@router.get("/", response_model=CartResponse)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart = get_or_create_user_cart(current_user.id, db)
    return calculate_cart_details(cart)


# 2. POST /cart/add (Add product to cart)
@router.post("/add", response_model=CartResponse, status_code=status.HTTP_200_OK)
def add_to_cart(
    item_in: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found"
        )

    if product.stock < item_in.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Insufficient stock available"
        )

    cart = get_or_create_user_cart(current_user.id, db)

    # Check if item already exists in cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item_in.product_id
    ).first()

    if existing_item:
        if product.stock < (existing_item.quantity + item_in.quantity):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Total requested quantity exceeds available stock"
            )
        existing_item.quantity += item_in.quantity
    else:
        new_item = CartItem(
            cart_id=cart.id, 
            product_id=product.id, 
            quantity=item_in.quantity
        )
        db.add(new_item)

    db.commit()
    db.refresh(cart)
    return calculate_cart_details(cart)


# 3. PUT /cart/update (Update quantity)
@router.put("/update", response_model=CartResponse)
def update_cart_item(
    item_in: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart = get_or_create_user_cart(current_user.id, db)
    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item_in.product_id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found in cart"
        )

    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if product.stock < item_in.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Requested quantity exceeds stock"
        )

    cart_item.quantity = item_in.quantity
    db.commit()
    db.refresh(cart)
    return calculate_cart_details(cart)


# 4. DELETE /cart/remove (Remove item from cart)
@router.delete("/remove", response_model=CartResponse)
def remove_from_cart(
    item_in: CartItemRemove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart = get_or_create_user_cart(current_user.id, db)
    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item_in.product_id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found in cart"
        )

    db.delete(cart_item)
    db.commit()
    db.refresh(cart)
    return calculate_cart_details(cart)