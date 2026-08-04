from fastapi import FastAPI
from core.database import engine, Base
from models import job
from routes.job_routes import router as job_router

app = FastAPI(title="Async Task Processing System")

# Create tables in MySQL automatically
Base.metadata.create_all(bind=engine)

# Include job API endpoints
app.include_router(job_router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "1.0.0"}