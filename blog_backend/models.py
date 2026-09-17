import enum
from datetime import datetime, timedelta
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.orm import relationship
from database import Base


class PlanType(str, enum.Enum):
    BASIC = "Basic"
    PREMIUM = "Premium"
    PRO = "Pro"


# Tiered limits lookup table
PLAN_LIMITS = {
    PlanType.BASIC: {
        "max_posts": 1,
        "max_images_per_post": 1,
        "max_likes": 5,
        "max_comments": 5,
    },
    PlanType.PREMIUM: {
        "max_posts": 2,
        "max_images_per_post": 2,
        "max_likes": 20,
        "max_comments": 20,
    },
    PlanType.PRO: {
        "max_posts": float("inf"),
        "max_images_per_post": float("inf"),
        "max_likes": float("inf"),
        "max_comments": float("inf"),
    },
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")

    # Subscription and Billing Relationships
    subscription = relationship(
        "SubscriptionPlan", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    billing_records = relationship(
        "BillingHistory", back_populates="user", cascade="all, delete-orphan"
    )


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    plan_name = Column(Enum(PlanType), default=PlanType.BASIC, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))
    is_active = Column(Integer, default=1)

    user = relationship("User", back_populates="subscription")


class BillingHistory(Base):
    __tablename__ = "billing_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    transaction_id = Column(String(100), unique=True, nullable=False)
    invoice_path = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="billing_records")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(300), nullable=True)  # <-- Image field
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")

    __table_args__ = (UniqueConstraint("post_id", "user_id", name="unique_post_user_like"),)