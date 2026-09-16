from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

try:
    from app.core.database import get_db
except (ImportError, ModuleNotFoundError):
    from core.database import get_db

try:
    from core.security import get_current_user
except (ImportError, ModuleNotFoundError):
    from app.core.security import get_current_user
try:
    from app.models.ecommerce_models import Product, User, RoleEnum
except (ImportError, ModuleNotFoundError):
    from models.ecommerce_models import Product, User, RoleEnum

router = APIRouter(prefix="/products", tags=["Products"])


# Schemas
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    category: str = "General"


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None


def require_admin(current_user: User = Depends(get_current_user)):
    user_role = str(
        getattr(current_user.role, "value", current_user.role)
    ).upper()
    if user_role not in ["ADMIN", "STAFF"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user


# 1. GET /products (Browse, Search, Price/Category Filtering & Sorting)
@router.get("")
def list_products(
    search: Optional[str] = Query(None, description="Search by name or description"),
    category: Optional[str] = Query(None, description="Filter by category string"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    sort_by: Optional[str] = Query(
        "newest",
        description="Sort by: newest, price_asc, price_desc, or popularity",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    # Search: name or description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
            )
        )

    # Category filter
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))

    # Price range filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(asc(Product.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Product.price))
    elif sort_by == "popularity":
        query = query.order_by(desc(Product.popularity))
    else:  # default: newest
        query = query.order_by(desc(Product.created_at))

    return query.offset(skip).limit(limit).all()


# 2. GET /products/{product_id} (Retrieve details & increment popularity)
@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found.",
        )

    # Increment popularity counter per view
    if hasattr(product, "popularity"):
        product.popularity = (product.popularity or 0) + 1
        db.commit()
        db.refresh(product)

    return product


# 3. POST /products (Admin Only)
@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    new_product = Product(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock=payload.stock,
        category=payload.category,
        popularity=0.0,
        created_at=datetime.utcnow(),
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


# 4. PUT /products/{product_id} (Admin Only)
@router.put("/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


# 5. DELETE /products/{product_id} (Admin Only)
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )
    db.delete(product)
    db.commit()
    return None