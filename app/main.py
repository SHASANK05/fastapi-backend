from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.routes import auth_routes, product_routes, cart_routes, checkout_routes
from app.routes import notification_routes
from .routes.order_routes import router as order_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart E-Commerce API",
    description="User Panel APIs, Authentication, Product Catalog, Cart, and Stripe Checkout",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(cart_routes.router)
app.include_router(checkout_routes.router)
app.include_router(notification_routes.router)
app.include_router(order_router)


@app.get("/")
def root():
    return {"message": "Smart E-Commerce API is running"}