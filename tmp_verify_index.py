import sys
import os
from sqlalchemy import text
import shared_database

def verify_search_index():
    if not shared_database.SyncSessionLocal:
        print("SyncSessionLocal not initialized")
        return

    db = shared_database.SyncSessionLocal()
    try:
        count = db.execute(text("SELECT COUNT(*) FROM search.property_index")).scalar()
        print(f"Total Search Index Count: {count}")
    except Exception as e:
        print(f"Error querying search index: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_search_index()
