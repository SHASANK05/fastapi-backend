from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.routes import auth_routes, product_routes, cart_routes, checkout_routes

# Create all database tables (including orders & payments)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart E-Commerce API",
    description="User Panel APIs, Authentication, Product Catalog, Cart, and Stripe Checkout",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all route handlers
app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(cart_routes.router)
app.include_router(checkout_routes.router)


@app.get("/")
def root():
    return {"message": "Smart E-Commerce API is running"}