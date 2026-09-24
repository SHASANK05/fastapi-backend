import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models
from routers import (
    auth_routes,
    post_routes,
    interaction_routes,
    subscription_routes,
    notification_routes,
)
from routers.dashboard_routes import router as dashboard_router
from routers.ai_support_routes import router as ai_support_router

# 1. Create all database tables (including ChatLog, Notification, etc.)
Base.metadata.create_all(bind=engine)

# 2. Ensure upload directories exist
os.makedirs("media/posts", exist_ok=True)
os.makedirs("media/invoices", exist_ok=True)

# 3. Instantiate FastAPI application first
app = FastAPI(title="Blog Management API", version="2.0.0")

# 4. CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Mount static directories
app.mount("/media", StaticFiles(directory="media"), name="media")

# 6. Register all application routers
app.include_router(auth_routes.router)
app.include_router(post_routes.router)
app.include_router(interaction_routes.router)
app.include_router(subscription_routes.router)
app.include_router(dashboard_router)
app.include_router(notification_routes.router)
app.include_router(ai_support_router)


@app.get("/")
def root():
    return {
        "message": "Blog Management API with Media, Search, Billing, Notifications, and AI Support is running"
    }