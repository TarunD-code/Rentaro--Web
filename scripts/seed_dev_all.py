import sqlite3
import json
import os
import datetime

# Database paths
DB_CONFIG = {
    "auth": "rentora_auth.db",
    "properties": "rentora_properties.db",
    "notifications": "rentora_notification.db",
    "profile": "rentora_profile.db"
}

FIXTURES_PATH = "scripts/fixtures.json"

def seed_auth_and_profile(auth_cur, prof_cur, users):
    print("Seeding Auth & Profile Services...")
    auth_cur.execute("DELETE FROM users")
    prof_cur.execute("DELETE FROM profiles")
    
    for user in users:
        # Auth entry
        auth_cur.execute(
            "INSERT INTO users (email_or_phone, hashed_password, role, is_verified) VALUES (?, ?, ?, ?)",
            (user["email"], "pbkdf2:sha256:260000$mock_hash", user["role"], 1)
        )
        # Profile entry
        prof_cur.execute(
            "INSERT INTO profiles (user_identifier, full_name, kyc_status, email, address) VALUES (?, ?, ?, ?, ?)",
            (user["email"], user["full_name"], "verified" if user["is_kyc_verified"] else "pending", user["email"], "Bengaluru, India")
        )

def seed_properties(cursor, properties):
    print("Seeding Property Service...")
    cursor.execute("DELETE FROM properties")
    for prop in properties:
        cursor.execute(
            "INSERT INTO properties (title, address, price, owner_id, property_type, amenities) VALUES (?, ?, ?, ?, ?, ?)",
            (prop["title"], prop["address"], prop["rent"], "owner@rentora.com", "Apartment", ",".join(prop["amenities"]))
        )

def seed_all():
    if not os.path.exists(FIXTURES_PATH):
        print(f"Error: Fixtures not found at {FIXTURES_PATH}")
        return

    with open(FIXTURES_PATH, 'r') as f:
        data = json.load(f)

    # Connections
    conn_auth = sqlite3.connect(DB_CONFIG["auth"])
    conn_prof = sqlite3.connect(DB_CONFIG["profile"])
    conn_prop = sqlite3.connect(DB_CONFIG["properties"])

    try:
        seed_auth_and_profile(conn_auth.cursor(), conn_prof.cursor(), data["users"])
        seed_properties(conn_prop.cursor(), data["properties"])
        
        conn_auth.commit()
        conn_prof.commit()
        conn_prop.commit()
        print("\nMaster Seed Complete! Databases are now populated with realistic test data.")
    except Exception as e:
        print(f"\nSeeding Failed: {e}")
        conn_auth.rollback()
        conn_prof.rollback()
        conn_prop.rollback()
    finally:
        conn_auth.close()
        conn_prof.close()
        conn_prop.close()

if __name__ == "__main__":
    seed_all()
