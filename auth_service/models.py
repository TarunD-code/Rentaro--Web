from sqlalchemy import Boolean, Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email_or_phone = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # "tenant" or "owner"
    is_verified = Column(Boolean, default=False)
