from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.ecommerce_models import RoleEnum, OrderStatusEnum, PaymentStatusEnum


# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., example="Wireless Noise Cancelling Headphones")
    description: Optional[str] = Field(None, example="High fidelity audio")
    price: float = Field(..., gt=0, example=2999.00)
    category: str = Field(..., example="Electronics")
    stock: int = Field(..., ge=0, example=20)
    popularity: Optional[float] = Field(0.0, ge=0.0, le=5.0, example=4.5)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Cart Schemas
class CartItemAdd(BaseModel):
    product_id: int = Field(..., example=1)
    quantity: int = Field(1, ge=1, example=2)


class CartItemUpdate(BaseModel):
    product_id: int = Field(..., example=1)
    quantity: int = Field(..., ge=1, example=3)


class CartItemRemove(BaseModel):
    product_id: int = Field(..., example=1)


CartItemDelete = CartItemRemove


class CartItemResponse(BaseModel):
    product_id: int
    name: str
    unit_price: float
    quantity: int
    item_total: float


class CartResponse(BaseModel):
    cart_id: int
    user_id: int
    items: List[CartItemResponse]
    cart_total: float
    tax_amount: float
    grand_total: float


# Checkout & Order Schemas
class CheckoutResponse(BaseModel):
    order_id: int
    amount: float
    currency: str
    tax_amount: float
    payment_status: PaymentStatusEnum
    order_status: OrderStatusEnum
    payment_intent_id: Optional[str] = None
    client_secret: Optional[str] = None
    stripe_session_id: str
    checkout_url: str
    message: str


class OrderItemDetail(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    item_total: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total: float
    tax_amount: float
    payment_status: PaymentStatusEnum
    order_status: OrderStatusEnum
    created_at: datetime
    items: List[OrderItemDetail]

    class Config:
        from_attributes = True


class PaymentConfirmRequest(BaseModel):
    order_id: int
    transaction_id: Optional[str] = "txn_mock_stripe_success"


class PaymentIntentResponse(BaseModel):
    order_id: int
    amount: float
    currency: str
    payment_intent_id: str
    client_secret: str