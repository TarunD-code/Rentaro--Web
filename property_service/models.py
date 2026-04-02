from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, index=True) # References user_identifier
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    address = Column(String, nullable=False) # Full address
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, default="India")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    amenities = Column(String, nullable=True) # Stored as comma separated string for MVP
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    media = relationship("PropertyMedia", back_populates="property")

class PropertyMedia(Base):
    __tablename__ = "property_media"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    file_type = Column(String) # image, video
    raw_url = Column(String) # Raw S3/CDN URL
    thumb_url = Column(String, nullable=True) # Thumbnail URL
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True) # in bytes
    width = Column(Integer, nullable=True) # in pixels
    height = Column(Integer, nullable=True)
    
    property = relationship("Property", back_populates="media")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
