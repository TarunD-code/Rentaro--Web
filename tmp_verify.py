import sys
import os
from sqlalchemy import text
import shared_database

def verify_db():
    if not shared_database.SyncSessionLocal:
        print("SyncSessionLocal not initialized")
        return

    db = shared_database.SyncSessionLocal()
    try:
        count = db.execute(text("SELECT COUNT(*) FROM property.properties")).scalar()
        print(f"Total Property Count: {count}")
        
        result = db.execute(text("SELECT id, title, price, lat, lng, city, status FROM property.properties LIMIT 5"))
        print("First 5 records:")
        for row in result:
            print(f"ID: {row.id}, Title: {row.title}, Price: {row.price}, Lat: {row.lat}, Lng: {row.lng}, City: {row.city}, Status: {row.status}")
            
        media_count = db.execute(text("SELECT COUNT(*) FROM property.property_media")).scalar()
        print(f"Total Property Media Count: {media_count}")
        
    except Exception as e:
        print(f"Error querying properties: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_db()
