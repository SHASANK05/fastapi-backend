from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Card(Base):
    __tablename__ = "cards_card"

    id = Column(BigInteger, primary_key=True, index=True)
    cardholder_name = Column(String(150))
    masked_card = Column(String(19))
    last_4 = Column(String(4))
    card_type = Column(String(20))
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)
    user_id = Column(BigInteger, nullable=False)

class Transaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    card_id = Column(BigInteger, ForeignKey("cards_card.id"), nullable=False)
    merchant_name = Column(String(150), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED
    failure_reason = Column(String(255), nullable=True)
    transaction_reference = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())