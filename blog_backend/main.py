from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from database import engine, Base
import models
from routers import auth_routes, post_routes, interaction_routes, subscription_routes

# Create all tables (including subscription_plans and billing_history)
Base.metadata.create_all(bind=engine)

# Ensure upload directories exist
os.makedirs("media/posts", exist_ok=True)
os.makedirs("media/invoices", exist_ok=True)

app = FastAPI(title="Blog Management API", version="2.0.0")

# Mount /media static directory (serves both /media/posts and /media/invoices)
app.mount("/media", StaticFiles(directory="media"), name="media")

# Include routers
app.include_router(auth_routes.router)
app.include_router(post_routes.router)
app.include_router(interaction_routes.router)
app.include_router(subscription_routes.router)

@app.get("/")
def root():
    return {"message": "Blog Management API with Media, Search, and Billing is running"}