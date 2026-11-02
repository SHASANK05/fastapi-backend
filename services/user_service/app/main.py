from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import UserProfile, Address
from app.schemas import ProfileCreate, ProfileUpdate, ProfileResponse, AddressCreate, AddressResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="ShopEase User Profile & Address Service", version="1.0.0", lifespan=lifespan)

@app.get("/")
def root():
    return {"service": "User Service", "status": "operational", "port": 8002}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/users/profile", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    existing = db.query(UserProfile).filter(UserProfile.user_id == payload.user_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists for this user")
    
    profile = UserProfile(
        user_id=payload.user_id,
        full_name=payload.full_name,
        phone_number=payload.phone_number
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@app.get("/api/v1/users/profile/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile

@app.post("/api/v1/users/profile/{user_id}/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def add_address(user_id: int, address: AddressCreate, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found. Create profile first.")
    
    new_address = Address(
        user_profile_id=profile.id,
        street=address.street,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address
