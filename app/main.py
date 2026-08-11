from fastapi import FastAPI
from app.core.database import engine
from app.models.ecommerce_models import Base
from app.routes import auth_routes

# Automatically create User, Product, and Cart database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart E-Commerce API",
    description="User Panel APIs, Authentication, Cart & Order Management",
    version="1.0.0"
)

# Register Authentication Routes
app.include_router(auth_routes.router)

@app.get("/")
def root():
    return {"message": "Smart E-Commerce Backend Running Successfully"}