import sqlite3
import os

PROFILE_DB = "rentora_profile.db"
PROPERTY_DB = "rentora_properties.db"

def migrate_profile_db():
    print("Migrating Profile DB...")
    conn = sqlite3.connect(PROFILE_DB)
    cursor = conn.cursor()
    
    # Create Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id VARCHAR,
        receiver_id VARCHAR,
        property_id INTEGER,
        body VARCHAR,
        is_read BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_messages_sender_id ON messages (sender_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_messages_receiver_id ON messages (receiver_id)")
    
    # Create Notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id VARCHAR,
        type VARCHAR,
        content VARCHAR,
        is_read BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)")
    
    conn.commit()
    conn.close()
    print("Profile DB migrated successfully.")

def migrate_property_db():
    print("Migrating Property DB...")
    conn = sqlite3.connect(PROPERTY_DB)
    cursor = conn.cursor()
    
    # Create Reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER,
        reviewer_id VARCHAR,
        rating FLOAT NOT NULL,
        text VARCHAR,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_reviews_property_id ON reviews (property_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_reviews_reviewer_id ON reviews (reviewer_id)")
    
    conn.commit()
    conn.close()
    print("Property DB migrated successfully.")

if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    
    if os.path.exists(PROFILE_DB):
        migrate_profile_db()
    else:
        print(f"Warning: {PROFILE_DB} not found in current directory.")
        
    if os.path.exists(PROPERTY_DB):
        migrate_property_db()
    else:
        print(f"Warning: {PROPERTY_DB} not found in current directory.")
        
    print("Sprint 7 migrations complete.")
