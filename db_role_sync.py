import sqlite3
from passlib.context import CryptContext

def run_db_fix():
    conn = sqlite3.connect('rentora_auth.db')
    cursor = conn.cursor()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    email = "admin@rentaro.com"
    
    # Update if exists, or create if missing
    cursor.execute("SELECT * FROM users WHERE email_or_phone = ?", (email,))
    user = cursor.fetchone()
    
    if user:
        print(f"Updating {email} (role {user[3]}) to 'admin'...")
        cursor.execute("UPDATE users SET role = 'admin', is_verified = 1 WHERE email_or_phone = ?", (email,))
        conn.commit()
    else:
        print(f"User {email} not found. Creating a new Admin user...")
        hashed_pwd = pwd_context.hash("admin123")
        cursor.execute("INSERT INTO users (email_or_phone, hashed_password, role, is_verified) VALUES (?, ?, ?, ?)", (email, hashed_pwd, "admin", 1))
        conn.commit()
    
    # Also check admin@rentora.com for consistency
    cursor.execute("UPDATE users SET role = 'admin', is_verified = 1 WHERE email_or_phone = 'admin@rentora.com'")
    conn.commit()
    
    print("Database role normalization complete.")
    conn.close()

if __name__ == "__main__":
    run_db_fix()
