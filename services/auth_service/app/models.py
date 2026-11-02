import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime
from app.database import Base

class RoleEnum(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"

class UserAuth(Base):
    __tablename__ = "users_auth"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
