import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import recommendation_routes, product_routes

# 1. Directory setup - place app and backend folders at the head of sys.path
APP_DIR = Path(__file__).resolve().parent                # .../fastapi_backend/app
BACKEND_DIR = APP_DIR.parent                             # .../fastapi_backend
CORE_DIR = BACKEND_DIR / "core"
MODELS_DIR = APP_DIR / "models"
ROUTES_DIR = APP_DIR / "routes"

for folder in [str(APP_DIR), str(BACKEND_DIR), str(CORE_DIR), str(MODELS_DIR), str(ROUTES_DIR)]:
    if folder in sys.path:
        sys.path.remove(folder)
    sys.path.insert(0, folder)

# 2. Database setup
try:
    from app.core.database import Base, engine
except (ImportError, ModuleNotFoundError):
    try:
        from core.database import Base, engine
    except (ImportError, ModuleNotFoundError):
        from database import Base, engine

# 3. Router imports
try:
    from app.routes.auth import router as auth_router
except (ImportError, ModuleNotFoundError):
    from routes.auth import router as auth_router

try:
    from app.routes.product_routes import router as product_router
except (ImportError, ModuleNotFoundError):
    from routes.product_routes import router as product_router

try:
    from app.routes.cart_routes import router as cart_router
except (ImportError, ModuleNotFoundError):
    from routes.cart_routes import router as cart_router

try:
    from app.routes.order_routes import router as order_router
except (ImportError, ModuleNotFoundError):
    from routes.order_routes import router as order_router

try:
    from app.routes.review_routes import router as review_router
except (ImportError, ModuleNotFoundError):
    from routes.review_routes import router as review_router

try:
    from app.routes.recommendation_routes import router as recommendation_router
except (ImportError, ModuleNotFoundError):
    from routes.recommendation_routes import router as recommendation_router

try:
    from app.routes.inventory_routes import router as inventory_router
except (ImportError, ModuleNotFoundError):
    from routes.inventory_routes import router as inventory_router

try:
    from app.routes.coupon_routes import router as coupon_router
except (ImportError, ModuleNotFoundError):
    from routes.coupon_routes import router as coupon_router

try:
    from app.routes.notification_routes import router as notification_router
except (ImportError, ModuleNotFoundError):
    from routes.notification_routes import router as notification_router

try:
    from app.routes.admin_returns import router as admin_returns_router
except (ImportError, ModuleNotFoundError):
    try:
        from routes.admin_returns import router as admin_returns_router
    except (ImportError, ModuleNotFoundError):
        from admin_returns import router as admin_returns_router

# 4. Initialize database schema
Base.metadata.create_all(bind=engine)

# 5. FastAPI Application Instance
app = FastAPI(
    title="Smart E-Commerce API",
    description="APIs for Catalog, Orders, Reviews, Promotions, Notifications, and Admin Return Flow",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. Mount routers
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(review_router)
app.include_router(recommendation_router)
app.include_router(inventory_router)
app.include_router(coupon_router)
app.include_router(notification_router)
app.include_router(admin_returns_router)
app.include_router(recommendation_routes.router)
app.include_router(product_routes.router)


@app.get("/")
def root():
    return {"message": "Smart E-Commerce API is running"}