from fastapi import FastAPI
from database import engine, Base
from routers import auth_routes, post_routes, interaction_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Blog Management API",
    description="Mini blogging system with Posts, Comments, Likes, and Email Alerts",
    version="1.0.0"
)

app.include_router(auth_routes.router)
app.include_router(post_routes.router)
app.include_router(interaction_routes.router)