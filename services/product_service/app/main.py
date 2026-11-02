from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Product
from app.schemas import (
    ProductCreate, 
    ProductResponse, 
    StockReservationRequest, 
    StockReservationResponse
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="ShopEase Product & Inventory Service", version="1.0.0", lifespan=lifespan)

@app.get("/")
def root():
    return {"service": "Product Service", "status": "operational", "port": 8003}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.sku == product.sku).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product with this SKU already exists")
    
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.get("/api/v1/products", response_model=List[ProductResponse])
def list_products(
    category: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    return query.offset(skip).limit(limit).all()

@app.get("/api/v1/products/{sku}", response_model=ProductResponse)
def get_product_by_sku(sku: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@app.post("/api/v1/products/reserve", response_model=StockReservationResponse)
def reserve_stock(payload: StockReservationRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.sku == payload.sku).with_for_update().first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    if product.stock < payload.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Insufficient inventory. Available: {product.stock}, Requested: {payload.quantity}"
        )
    
    product.stock -= payload.quantity
    db.commit()
    db.refresh(product)
    
    return {
        "sku": product.sku,
        "reserved_quantity": payload.quantity,
        "remaining_stock": product.stock,
        "status": "RESERVED"
    }

@app.post("/api/v1/products/release", response_model=StockReservationResponse)
def release_stock(payload: StockReservationRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.sku == payload.sku).with_for_update().first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    product.stock += payload.quantity
    db.commit()
    db.refresh(product)
    
    return {
        "sku": product.sku,
        "reserved_quantity": payload.quantity,
        "remaining_stock": product.stock,
        "status": "RELEASED"
    }
