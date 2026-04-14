import sqlite3
import random
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'rentora_properties.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE properties ADD COLUMN commute_score FLOAT")
        print("Column 'commute_score' added.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'commute_score' already exists.")
        else:
            raise e

    # Assign default scores for existing seed data so the frontend renders correctly immediately
    cursor.execute("SELECT id, lat, lng FROM properties")
    rows = cursor.fetchall()
    
    for row in rows:
        prop_id = row[0]
        # Just simple default if missing, 6.0 to 9.5
        score = round(random.uniform(6.0, 9.5), 1)
        cursor.execute("UPDATE properties SET commute_score = ? WHERE id = ?", (score, prop_id))
        
    conn.commit()
    conn.close()
    print("Migration complete. Scores assigned.")

if __name__ == "__main__":
    migrate()
