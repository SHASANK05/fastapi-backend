from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PaymentRequest(BaseModel):
    card_id: int
    amount: float = Field(..., gt=0, description="Amount must be greater than zero")
    merchant_name: str
    cvv: str = Field(..., min_length=3, max_length=4)

class PaymentResponse(BaseModel):
    transaction_id: int
    reference_id: str
    merchant: str
    amount: float
    currency: str
    status: str
    failure_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RecentTransaction(BaseModel):
    id: int
    amount: float
    masked_card_number: str
    date: datetime
    status: str
    merchant_name: Optional[str] = "N/A"

    class Config:
        from_attributes = True        

class DashboardSummaryResponse(BaseModel):
    total_transactions: int
    total_amount_spent: float
    current_month_spending: float
    available_credit_limit: float
    last_5_transactions: List[RecentTransaction]        