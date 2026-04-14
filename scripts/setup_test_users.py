import sqlite3
import os
import sys
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password): return pwd_context.hash(password)

AUTH_DB = "rentora_auth.db"
PROFILE_DB = "rentora_profile.db"

def setup():
    users = [
        {"email": "admin@rentora.com", "password": "admin123", "role": "admin", "full_name": "Rentora Admin"},
        {"email": "owner@rentora.com", "password": "owner123", "role": "owner", "full_name": "Property Owner"},
        {"email": "tenant@rentora.com", "password": "tenant123", "role": "tenant", "full_name": "App Tenant"}
    ]
    
    auth_conn = sqlite3.connect(AUTH_DB)
    prof_conn = sqlite3.connect(PROFILE_DB)
    
    for u in users:
        email = u["email"]
        hashed = get_password_hash(u["password"])
        role = u["role"]
        
        # Auth
        c = auth_conn.cursor()
        print(f"Checking auth for {email}...")
        c.execute("SELECT id FROM users WHERE email_or_phone = ?", (email,))
        row = c.fetchone()
        if row:
            print(f"Updating auth: {email}")
            c.execute("UPDATE users SET hashed_password=?, role=?, is_verified=1 WHERE email_or_phone=?", (hashed, role, email))
        else:
            print(f"Creating auth: {email}")
            c.execute("INSERT INTO users (email_or_phone, hashed_password, role, is_verified) VALUES (?, ?, ?, ?)", (email, hashed, role, 1))
            
        # Profile
        cp = prof_conn.cursor()
        print(f"Checking profile for {email}...")
        cp.execute("SELECT id FROM profiles WHERE user_identifier = ?", (email,))
        prow = cp.fetchone()
        if prow:
            print(f"Updating profile: {email}")
            cp.execute("UPDATE profiles SET full_name=?, kyc_status='verified' WHERE user_identifier=?", (u["full_name"], email))
        else:
            print(f"Creating profile: {email}")
            cp.execute("INSERT INTO profiles (user_identifier, full_name, email, kyc_status) VALUES (?, ?, ?, ?)", (email, u["full_name"], email, 'verified'))
            
    auth_conn.commit()
    prof_conn.commit()
    auth_conn.close()
    prof_conn.close()
    print("All users setup successfully.")

if __name__ == "__main__":
    setup()
