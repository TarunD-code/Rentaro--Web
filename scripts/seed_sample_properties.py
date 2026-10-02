import sys
import os
import logging
import random
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database
from property_service import models as property_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_sample_properties")

SAMPLE_PROPERTIES = [
    {
        "title": "Luxury Sea-View Apartment in Bandra",
        "description": "A beautiful 3BHK apartment with unhindered sea views, fully furnished with premium amenities.",
        "address": "Carter Road, Bandra West",
        "city": "Mumbai",
        "state": "Maharashtra",
        "lat": 19.0688,
        "lng": 72.8222,
        "price": 150000.0,
        "property_type": "Apartment",
        "amenities": "Gym,Swimming Pool,Security,Furnished,Sea View",
        "is_featured": True,
        "images": ["https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&q=80"]
    },
    {
        "title": "Cozy 1BHK in Indiranagar",
        "description": "Perfect for young professionals, walking distance to metro and restaurants.",
        "address": "100 Feet Road, Indiranagar",
        "city": "Bangalore",
        "state": "Karnataka",
        "lat": 12.9784,
        "lng": 77.6408,
        "price": 35000.0,
        "property_type": "Apartment",
        "amenities": "Semi-Furnished,Parking,Power Backup",
        "images": ["https://images.unsplash.com/photo-1502672260266-1c1e5250ad99?w=800&q=80"]
    },
    {
        "title": "Premium Independent Villa",
        "description": "Spacious 4BHK villa with a private garden and 24/7 security in a gated community.",
        "address": "Jubilee Hills",
        "city": "Hyderabad",
        "state": "Telangana",
        "lat": 17.4325,
        "lng": 78.4071,
        "price": 250000.0,
        "property_type": "Villa",
        "amenities": "Garden,Security,Clubhouse,Parking,Pet Friendly",
        "is_featured": True,
        "images": ["https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&q=80"]
    },
    {
        "title": "Modern Commercial Office Space",
        "description": "Ready-to-move office space suitable for IT startups with plug-and-play setup.",
        "address": "Cyber City, DLF Phase 2",
        "city": "Gurgaon",
        "state": "Haryana",
        "lat": 28.4950,
        "lng": 77.0895,
        "price": 450000.0,
        "property_type": "Commercial",
        "amenities": "Central AC,Cafeteria,Conference Room,High Speed Internet",
        "images": ["https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80"]
    },
    {
        "title": "Budget PG for Men",
        "description": "Twin sharing rooms with home-cooked food, high-speed Wi-Fi and daily housekeeping.",
        "address": "Koramangala 5th Block",
        "city": "Bangalore",
        "state": "Karnataka",
        "lat": 12.9352,
        "lng": 77.6245,
        "price": 12000.0,
        "property_type": "PG/Shared",
        "amenities": "Wi-Fi,Meals Included,Housekeeping,Washing Machine",
        "images": ["https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=800&q=80"]
    },
    {
        "title": "Affordable 2BHK Near Tech Park",
        "description": "Well ventilated 2BHK close to Manyata Tech Park. Ideal for techies.",
        "address": "Hebbal",
        "city": "Bangalore",
        "state": "Karnataka",
        "lat": 13.0354,
        "lng": 77.5988,
        "price": 28000.0,
        "property_type": "Apartment",
        "amenities": "Gym,Security,Power Backup",
        "images": ["https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80"]
    },
    {
        "title": "Lavish Penthouse with Terrace",
        "description": "Exquisite 5BHK penthouse offering panoramic city views and a private terrace.",
        "address": "Nungambakkam",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "lat": 13.0604,
        "lng": 80.2496,
        "price": 300000.0,
        "property_type": "Apartment",
        "amenities": "Terrace,Pool,Gym,Security,Fully Furnished",
        "images": ["https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&q=80"]
    },
    {
        "title": "Retail Shop space in High Street",
        "description": "Ground floor retail space on a bustling street, ideal for boutiques or cafes.",
        "address": "Connaught Place",
        "city": "New Delhi",
        "state": "Delhi",
        "lat": 28.6304,
        "lng": 77.2177,
        "price": 550000.0,
        "property_type": "Commercial",
        "amenities": "Street Facing,Parking,High Footfall",
        "images": ["https://images.unsplash.com/photo-1534489240827-cb52f01f0164?w=800&q=80"]
    },
    {
        "title": "Co-living Space for Women",
        "description": "Safe and vibrant co-living space with single and double occupancy options.",
        "address": "Viman Nagar",
        "city": "Pune",
        "state": "Maharashtra",
        "lat": 18.5679,
        "lng": 73.9143,
        "price": 14000.0,
        "property_type": "PG/Shared",
        "amenities": "Wi-Fi,Security,Gym,Lounge Area",
        "images": ["https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=800&q=80"]
    },
    {
        "title": "Spacious 3BHK for Families",
        "description": "Family-friendly society with kids play area and clubhouse.",
        "address": "Powai",
        "city": "Mumbai",
        "state": "Maharashtra",
        "lat": 19.1176,
        "lng": 72.9060,
        "price": 85000.0,
        "property_type": "Apartment",
        "amenities": "Kids Play Area,Clubhouse,Parking,Security",
        "images": ["https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80"]
    },
    {
        "title": "Studio Apartment in City Center",
        "description": "Compact and fully furnished studio apartment for a minimalist lifestyle.",
        "address": "MG Road",
        "city": "Bangalore",
        "state": "Karnataka",
        "lat": 12.9716,
        "lng": 77.5946,
        "price": 25000.0,
        "property_type": "Apartment",
        "amenities": "Fully Furnished,AC,Wi-Fi",
        "images": ["https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800&q=80"]
    },
    {
        "title": "Eco-friendly Row House",
        "description": "Beautiful 3BHK row house with solar heating and rainwater harvesting.",
        "address": "Whitefield",
        "city": "Bangalore",
        "state": "Karnataka",
        "lat": 12.9698,
        "lng": 77.7499,
        "price": 65000.0,
        "property_type": "Villa",
        "amenities": "Solar Power,Garden,Security,Pet Friendly",
        "images": ["https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&q=80"]
    },
    {
        "title": "Warehouse / Godown Space",
        "description": "Large 5000 sq ft warehouse with easy truck access and high ceilings.",
        "address": "Peenya Industrial Area",
        "city": "Bangalore",
        "state": "Karnataka",
        "lat": 13.0285,
        "lng": 77.5197,
        "price": 120000.0,
        "property_type": "Commercial",
        "amenities": "Loading Dock,Security,Parking",
        "images": ["https://images.unsplash.com/photo-1586528116311-ad8ed745d44c?w=800&q=80"]
    },
    {
        "title": "Beachfront 2BHK Retreat",
        "description": "Wake up to the sound of waves in this serene beachfront property.",
        "address": "Calangute",
        "city": "Goa",
        "state": "Goa",
        "lat": 15.5494,
        "lng": 73.7535,
        "price": 50000.0,
        "property_type": "Apartment",
        "amenities": "Beach Access,Pool,Furnished,Air Conditioning",
        "images": ["https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=800&q=80"]
    },
    {
        "title": "Fully Furnished IT Guest House",
        "description": "Ideal for corporate rentals, features 6 bedrooms and daily housekeeping.",
        "address": "Madhapur",
        "city": "Hyderabad",
        "state": "Telangana",
        "lat": 17.4483,
        "lng": 78.3915,
        "price": 180000.0,
        "property_type": "Villa",
        "amenities": "Fully Furnished,Housekeeping,Wi-Fi,Parking",
        "images": ["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&q=80"]
    }
]

def seed_properties():
    if not shared_database.SyncSessionLocal:
        logger.error("SyncSessionLocal not initialized")
        return

    logger.info("Connecting to PostgreSQL to seed properties...")
    db = shared_database.SyncSessionLocal()
    
    try:
        # Clear existing
        db.query(property_models.PropertyMedia).delete()
        db.query(property_models.Property).delete()
        
        owner_id = "admin@rentaro.com"
        
        for data in SAMPLE_PROPERTIES:
            images = data.pop("images", [])
            
            prop = property_models.Property(
                owner_id=owner_id,
                title=data["title"],
                description=data["description"],
                address=data["address"],
                city=data["city"],
                state=data["state"],
                lat=data["lat"],
                lng=data["lng"],
                price=data["price"],
                property_type=data["property_type"],
                amenities=data["amenities"],
                is_featured=data.get("is_featured", False),
                status="available",
                available_from=datetime.datetime.utcnow(),
                is_verified=True,
                owner_verified=True,
                is_furnished="Furnished" in data["amenities"],
                is_pet_friendly="Pet Friendly" in data["amenities"]
            )
            
            db.add(prop)
            db.commit()
            db.refresh(prop)
            
            for img_url in images:
                media = property_models.PropertyMedia(
                    property_id=prop.id,
                    file_type="image",
                    raw_url=img_url,
                    thumb_url=img_url
                )
                db.add(media)
                
            db.commit()
            logger.info(f"Seeded property: {prop.title}")
            
        logger.info(f"✅ Successfully seeded 15 properties.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed properties: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_properties()
