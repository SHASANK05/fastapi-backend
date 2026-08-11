import enum
from sqlalchemy import Column, Integer, String, Float, Text, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True) 
    role = Column(Enum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    images = Column(JSON, default=[], nullable=True) 


    carts = relationship("Cart", back_populates="product", cascade="all, delete-orphan")

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    user = relationship("User", back_populates="carts")
    product = relationship("Product", back_populates="carts")