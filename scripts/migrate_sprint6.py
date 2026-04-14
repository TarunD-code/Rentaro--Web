import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_DB = os.path.join(BASE_DIR, "rentora_profile.db")
PROPERTY_DB = os.path.join(BASE_DIR, "rentora_properties.db")

def migrate_profiles():
    print("Migrating rentora_profile.db...")
    try:
        conn = sqlite3.connect(PROFILE_DB)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE profiles ADD COLUMN age INTEGER;")
        cursor.execute("ALTER TABLE profiles ADD COLUMN phone_number VARCHAR;")
        cursor.execute("ALTER TABLE profiles ADD COLUMN permanent_address VARCHAR;")
        cursor.execute("ALTER TABLE profiles ADD COLUMN photo_url VARCHAR;")
        conn.commit()
        print("Successfully migrated profiles.")
    except sqlite3.OperationalError as e:
        print(f"Profiles migration skipped or failed: {e}")
    finally:
        conn.close()

def migrate_properties():
    print("Migrating rentora_properties.db...")
    try:
        conn = sqlite3.connect(PROPERTY_DB)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE properties ADD COLUMN property_type VARCHAR DEFAULT 'Apartment';")
        conn.commit()
        print("Successfully migrated properties.")
    except sqlite3.OperationalError as e:
        print(f"Properties migration skipped or failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_profiles()
    migrate_properties()
