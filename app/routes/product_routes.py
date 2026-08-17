from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.ecommerce_models import Product
from app.schemas.ecommerce_schemas import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["Product Catalog"])


# 1. POST /products (Create a product for testing & catalog population)
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# 2. GET /products (Multi-filtering: category, price range, stock, popularity)
@router.get("/", response_model=List[ProductResponse])
def get_all_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock_only: Optional[bool] = Query(False, description="Show only in-stock items"),
    sort_by: Optional[str] = Query("popularity_desc", description="Sort by: popularity_desc, price_asc, price_desc"),
    db: Session = Depends(get_db)
):
    query = db.query(Product)

    # Category filter
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))

    # Price range filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Stock availability filter
    if in_stock_only:
        query = query.filter(Product.stock > 0)

    # Popularity & Price Sorting
    if sort_by == "popularity_desc":
        query = query.order_by(Product.popularity.desc())
    elif sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())

    return query.all()


# 3. GET /products/category/{category} (Direct category endpoint)
@router.get("/category/{category}", response_model=List[ProductResponse])
def get_products_by_category(category: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.category.ilike(category)).all()
    return products


# 4. GET /products/{id} (Get single product by ID)
@router.get("/{id}", response_model=ProductResponse)
def get_product_by_id(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found"
        )
    return product