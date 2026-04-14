import sqlite3
import os

DB_PATH = 'rentora_profile.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(profiles)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    
    new_cols = [
        ('first_name', 'TEXT'),
        ('last_name', 'TEXT'),
        ('full_name', 'TEXT'),
        ('email', 'TEXT'),
        ('date_of_birth', 'TEXT'),
        ('age', 'INTEGER'),
        ('phone_number', 'TEXT'),
        ('address', 'TEXT'),
        ('permanent_address', 'TEXT'),
        ('photo_url', 'TEXT'),
        ('kyc_status', 'TEXT DEFAULT "not_submitted"'),
        ('updated_at', 'DATETIME')
    ]
    
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            print(f"Adding column {col_name} to profiles...")
            try:
                cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
    
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
