from typing import Optional
from pydantic import BaseModel, Field

class PaymentProcessRequest(BaseModel):
    order_id: int
    amount: float = Field(..., gt=0)
    payment_method: str = "UPI"
    simulate_failure: bool = False

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    status: str
    transaction_ref: Optional[str] = None

    class Config:
        from_attributes = True
