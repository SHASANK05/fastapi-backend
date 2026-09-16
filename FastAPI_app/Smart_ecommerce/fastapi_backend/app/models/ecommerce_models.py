import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Float,
    Text,
    Enum as SQLEnum,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

try:
    from app.core.database import Base
except (ImportError, ModuleNotFoundError):
    try:
        from core.database import Base
    except (ImportError, ModuleNotFoundError):
        from database import Base


# --- Enum Definitions ---
class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    CUSTOMER = "CUSTOMER"


class OrderStatusEnum(str, enum.Enum):
    RETURNED = "returned"
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatusEnum(str, enum.Enum):
    REFUNDED = "refunded"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class NotificationTypeEnum(str, enum.Enum):
    RETURN_APPROVED = "Return approved"
    RETURN_REJECTED = "Return rejected"
    REFUND_COMPLETED = "Refund completed"
    ORDER_CONFIRMED = "Order confirmed"
    PAYMENT_SUCCESS = "Payment successful"
    PAYMENT_FAILED = "Payment failed"
    ORDER_SHIPPED = "Order shipped"
    ORDER_DELIVERED = "Order delivered"
    CART_UPDATED = "Cart updated"


# --- Models ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)
    role = Column(
        SQLEnum(RoleEnum, values_callable=lambda x: [e.value for e in x]),
        default=RoleEnum.CUSTOMER,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    cart = relationship(
        "Cart", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    orders = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(100), index=True, nullable=False, default="General")
    stock = Column(Integer, default=0, nullable=False)
    popularity = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    cart_items = relationship(
        "CartItem", back_populates="product", cascade="all, delete-orphan"
    )
    order_items = relationship("OrderItem", back_populates="product")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cart")
    items = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    payment_status = Column(
        SQLEnum(PaymentStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )
    order_status = Column(
        SQLEnum(OrderStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=OrderStatusEnum.PENDING,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    payment = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    item_total = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(
        Integer, ForeignKey("orders.id"), unique=True, nullable=False
    )
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="inr", nullable=False)
    payment_method = Column(String(50), default="stripe", nullable=False)
    transaction_id = Column(String(255), nullable=True)
    status = Column(
        SQLEnum(PaymentStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )
    timestamp = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(
        SQLEnum(
            NotificationTypeEnum, values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
    )
    message = Column(String(500), nullable=False)
    read_status = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String(255), nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(String(20), default="approved")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="reviews")
    product = relationship("Product", backref="reviews")


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    discount_percent = Column(Float, nullable=False)
    max_discount_amount = Column(Float, nullable=True)
    min_order_amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)