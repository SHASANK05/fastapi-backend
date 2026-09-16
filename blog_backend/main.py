from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from database import engine, Base
from routers import auth_routes, post_routes, interaction_routes

# Create tables
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs("media/posts", exist_ok=True)

app = FastAPI(title="Blog Management API", version="2.0.0")

# Mount /media static directory
app.mount("/media", StaticFiles(directory="media"), name="media")

# Include routers
app.include_router(auth_routes.router)
app.include_router(post_routes.router)
app.include_router(interaction_routes.router)

@app.get("/")
def root():
    return {"message": "Blog Management API with Media and Search is running"}