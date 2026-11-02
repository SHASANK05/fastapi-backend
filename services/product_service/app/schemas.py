from typing import Optional
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: str

class ProductResponse(ProductCreate):
    id: int

    class Config:
        from_attributes = True

class StockReservationRequest(BaseModel):
    sku: str
    quantity: int = Field(..., gt=0)

class StockReservationResponse(BaseModel):
    sku: str
    reserved_quantity: int
    remaining_stock: int
    status: str
