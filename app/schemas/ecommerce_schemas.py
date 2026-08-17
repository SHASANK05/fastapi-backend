from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ================= PRODUCT SCHEMAS =================
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    stock: int = 0
    popularity: float = 0.0


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ================= CART SCHEMAS =================
class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)


class CartItemRemove(BaseModel):
    product_id: int


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