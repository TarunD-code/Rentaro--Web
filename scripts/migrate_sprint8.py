import sqlite3
import os

PROFILE_DB = "rentora_profile.db"
AUTH_DB = "rentora_auth.db"

def migrate_profile_db():
    print("Migrating Profile DB for Sprint 8...")
    conn = sqlite3.connect(PROFILE_DB)
    cursor = conn.cursor()
    
    # Check existing columns to avoid duplicate column errors
    cursor.execute("PRAGMA table_info(profiles)")
    columns = [col[1] for col in cursor.fetchall()]
    
    new_cols = [
        ("first_name", "VARCHAR"),
        ("last_name", "VARCHAR"),
        ("email", "VARCHAR"),
        ("city", "VARCHAR"),
        ("state", "VARCHAR"),
        ("pincode", "VARCHAR")
    ]
    
    for col_name, col_type in new_cols:
        if col_name not in columns:
            print(f"Adding column '{col_name}' to 'profiles'")
            cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")
            
    conn.commit()
    conn.close()
    print("Profile DB migrated.")

if __name__ == "__main__":
    try:
        migrate_profile_db()
        print("Sprint 8 Migration Completed Successfully.")
    except Exception as e:
        print(f"Migration Failed: {str(e)}")
