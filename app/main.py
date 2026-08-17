from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.routes import auth_routes, product_routes, cart_routes

# Automatically create User, Product, Cart, and CartItem database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart E-Commerce API",
    description="User Panel APIs, Authentication, Product Catalog & Cart Management",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All Routes
app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(cart_routes.router)


@app.get("/")
def root():
    return {"message": "Smart E-Commerce Backend Running Successfully"}