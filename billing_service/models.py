from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class FeaturedProduct(Base):
    __tablename__ = "featured_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g., Bronze, Silver, Gold
    duration_days = Column(Integer, default=30)
    price_inr = Column(Float, nullable=False)
    priority = Column(Integer, default=1) # 1: Low, 2: Medium, 3: High
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class FeaturedPurchase(Base):
    __tablename__ = "featured_purchases"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, index=True)
    property_id = Column(Integer, index=True)
    product_id = Column(Integer, ForeignKey("featured_products.id"))
    transaction_status = Column(String, default="pending") # pending, completed, failed
    amount = Column(Float, nullable=False)
    razorpay_order_id = Column(String, unique=True, nullable=True)
    razorpay_payment_id = Column(String, unique=True, nullable=True)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("FeaturedProduct")
