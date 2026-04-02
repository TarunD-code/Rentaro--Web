import sqlite3
import os
import sys
from passlib.context import CryptContext

# Add project root to path for imports
sys.path.append(os.getcwd())

# Configuration (mirrors auth_service/main.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_PATH = "rentora_auth.db"

def get_password_hash(password):
    return pwd_context.hash(password)

def create_admin():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Specific credentials from requirements
    email = "admin@rentora.com"
    password = "testing123"
    role = "admin"
    is_verified = 1
    
    hashed_pwd = get_password_hash(password)
    
    try:
        # Check table columns first
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Use existing column names: email_or_phone, hashed_password
        cursor.execute("""
            INSERT OR REPLACE INTO users (email_or_phone, hashed_password, role, is_verified)
            VALUES (?, ?, ?, ?)
        """, (email, hashed_pwd, role, is_verified))
        conn.commit()
        print(f"Successfully created/updated admin user: {email}")
        print(f"Password: {password}")
        print(f"Role: {role}")
    except Exception as e:
        print(f"Error creating admin: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()
