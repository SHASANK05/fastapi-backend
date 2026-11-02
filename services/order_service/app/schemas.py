from pydantic import BaseModel, Field

class OrderCreateRequest(BaseModel):
    sku: str
    quantity: int = Field(..., gt=0)
    total_amount: float = Field(..., gt=0)
    simulate_payment_failure: bool = False

class OrderResponse(BaseModel):
    id: int
    user_id: int
    sku: str
    quantity: int
    total_amount: float
    status: str

    class Config:
        from_attributes = True
