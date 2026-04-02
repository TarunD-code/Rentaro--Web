from pydantic import BaseModel, root_validator
from typing import Optional, List
import datetime

class PropertyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    address: str
    price: float
    amenities: Optional[str] = None # e.g. "Pool, Gym, Parking"

class MediaItem(BaseModel):
    id: int
    type: str # image, video
    url: str
    thumbnailUrl: Optional[str]
    mime: Optional[str]
    size: Optional[int]

    class Config:
        orm_mode = True

class PropertyMediaOut(MediaItem): # Compatibility with previous code
    pass

class HostProfile(BaseModel):
    id: str
    name: str
    verified: bool
    responseTime: str

class GeoLocation(BaseModel):
    lat: Optional[float]
    lng: Optional[float]

class AddressDetail(BaseModel):
    city: Optional[str]
    state: Optional[str]
    country: str = "India"
    geo: Optional[GeoLocation]

class PropertyOut(BaseModel): # Listing card view
    id: int
    owner_id: str
    title: str
    description: Optional[str]
    address: str
    price: float
    amenities: Optional[str]
    created_at: datetime.datetime
    media: List[MediaItem] = []

    class Config:
        orm_mode = True

class PropertyDetail(BaseModel): # Full detail view
    id: int
    title: str
    description: Optional[str]
    price: float
    currency: str = "INR"
    address: AddressDetail
    amenities: List[str]
    media: List[MediaItem]
    host: HostProfile
    createdAt: datetime.datetime
    updatedAt: datetime.datetime

    class Config:
        orm_mode = True
