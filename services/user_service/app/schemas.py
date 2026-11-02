from typing import List, Optional
from pydantic import BaseModel

class AddressCreate(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "India"

class AddressResponse(AddressCreate):
    id: int
    user_profile_id: int

    class Config:
        from_attributes = True

class ProfileCreate(BaseModel):
    user_id: int
    full_name: str
    phone_number: Optional[str] = None

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone_number: Optional[str] = None
    addresses: List[AddressResponse] = []

    class Config:
        from_attributes = True
