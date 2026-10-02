import sqlite3
import bcrypt
import datetime
import json
import os

# Configuration
DB_PATHS = {
    "auth": "rentora_auth.db",
    "profile": "rentora_profile.db",
    "property": "rentora_properties_v2.db",
    "payment": "rentora_payments.db",
    "notification": "rentora_notifications.db",
    "agreements": "rentora_agreements.db"
}

def get_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

def seed():
    print("Starting Master Seed Engine...")
    
    # 1. Clear existing data
    for name, path in DB_PATHS.items():
        if not os.path.exists(path):
            print(f"Warning: {path} not found. Skipping...")
            continue
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        try:
            if name == "auth": 
                cur.execute("DROP TABLE IF EXISTS users")
                cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email_or_phone TEXT UNIQUE, hashed_password TEXT, role TEXT, is_verified INTEGER)")
            if name == "profile": 
                cur.execute("DROP TABLE IF EXISTS profiles")
                cur.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, user_identifier TEXT, full_name TEXT, email TEXT, kyc_status TEXT)")
            if name == "property":
                cur.execute("DROP TABLE IF EXISTS properties")
                cur.execute("CREATE TABLE properties (id INTEGER PRIMARY KEY, owner_id TEXT, title TEXT, description TEXT, address TEXT, price REAL, property_type TEXT, status TEXT, city TEXT)")
                cur.execute("DROP TABLE IF EXISTS rental_agreements")
                cur.execute("CREATE TABLE rental_agreements (id INTEGER PRIMARY KEY, property_id INTEGER, tenant_id TEXT, owner_id TEXT, status TEXT)")
            if name == "payment": 
                cur.execute("DROP TABLE IF EXISTS payment_transactions")
                cur.execute("CREATE TABLE payment_transactions (id INTEGER PRIMARY KEY, tenant_id TEXT, owner_id TEXT, property_id INTEGER, amount REAL, transaction_type TEXT, status TEXT, paid_at TEXT)")
            if name == "notification": 
                cur.execute("DROP TABLE IF EXISTS notification_history")
                cur.execute("CREATE TABLE notification_history (id INTEGER PRIMARY KEY, user_id TEXT, type TEXT, content TEXT, status TEXT, created_at TEXT, is_read INTEGER)")
            if name == "agreements": 
                cur.execute("DROP TABLE IF EXISTS agreements")
                cur.execute("CREATE TABLE agreements (id INTEGER PRIMARY KEY, agreement_key TEXT, property_id INTEGER, tenant_id TEXT, owner_id TEXT, status TEXT, created_at TEXT, updated_at TEXT)")
                cur.execute("DROP TABLE IF EXISTS agreement_audit")
                cur.execute("CREATE TABLE agreement_audit (id INTEGER PRIMARY KEY, agreement_id INTEGER, action TEXT, actor_id TEXT, details TEXT, timestamp TEXT)")
            conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Table error in {name}: {e}")
        finally:
            conn.close()

    # 2. Seed Users (Auth & Profile)
    conn_auth = sqlite3.connect(DB_PATHS["auth"])
    conn_prof = sqlite3.connect(DB_PATHS["profile"])
    
    users = []
    # 10 Tenants
    for i in range(1, 11):
        users.append({"email": f"tenant{i}@rentora.com", "role": "tenant", "name": f"Tenant User {i}"})
    # 10 Owners
    for i in range(1, 11):
        users.append({"email": f"owner{i}@rentora.com", "role": "owner", "name": f"Owner User {i}"})
    # 1 Admin
    users.append({"email": "admin@rentora.com", "role": "admin", "name": "Super Admin"})

    pw_hash = get_hash("password123")
    
    for user in users:
        conn_auth.execute(
            "INSERT INTO users (email_or_phone, hashed_password, role, is_verified) VALUES (?, ?, ?, ?)",
            (user["email"], pw_hash, user["role"], 1)
        )
        conn_prof.execute(
            "INSERT INTO profiles (user_identifier, full_name, email, kyc_status) VALUES (?, ?, ?, ?)",
            (user["email"], user["name"], user["email"], "verified")
        )
    
    conn_auth.commit()
    conn_prof.commit()
    print(f"Seeded {len(users)} users.")

    # 3. Seed Properties (Property Service)
    conn_prop = sqlite3.connect(DB_PATHS["property"])
    for i in range(1, 11):
        owner_id = f"owner{((i-1)%10)+1}@rentora.com"
        conn_prop.execute(
            "INSERT INTO properties (id, owner_id, title, description, address, price, property_type, status, city) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (i, owner_id, f"Premium Apartment {i}", "Luxury living with all amenities.", f"MG Road Street {i}, Bengaluru", 20000.0 + (i*1000), "Apartment", "available", "Bengaluru")
        )
    conn_prop.commit()
    print("Seeded 10 properties.")

    # 4. Seed Agreements (Standalone Agreements Service)
    conn_ag = sqlite3.connect(DB_PATHS["agreements"])
    for i in range(1, 11):
        tenant_id = f"tenant{i}@rentora.com"
        owner_id = f"owner{i}@rentora.com"
        status = "generated" if i % 2 == 0 else "draft"
        conn_ag.execute(
            "INSERT INTO agreements (id, agreement_key, property_id, tenant_id, owner_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (i, f"AG-TEST-{i}", i, tenant_id, owner_id, status, datetime.datetime.utcnow().isoformat(), datetime.datetime.utcnow().isoformat())
        )
    conn_ag.commit()
    print("Seeded 10 agreements in standalone service.")

    # 5. Seed Payments (Payment Service)
    conn_pay = sqlite3.connect(DB_PATHS["payment"])
    for i in range(1, 11):
        tenant_id = f"tenant{i}@rentora.com"
        owner_id = f"owner{i}@rentora.com"
        conn_pay.execute(
            "INSERT INTO payment_transactions (tenant_id, owner_id, property_id, amount, transaction_type, status, paid_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tenant_id, owner_id, i, 25000.0, "rent", "captured", datetime.datetime.utcnow().isoformat())
        )
    conn_pay.commit()
    print("Seeded 10 payment records.")

    # 6. Seed Notifications (Notification Service)
    conn_notif = sqlite3.connect(DB_PATHS["notification"])
    for i in range(1, 11):
        tenant_id = f"tenant{i}@rentora.com"
        for j in range(1, 3):
            conn_notif.execute(
                "INSERT INTO notification_history (user_id, type, content, status, created_at, is_read) VALUES (?, ?, ?, ?, ?, ?)",
                (tenant_id, "message", f"Test notification {j} for {tenant_id}", "sent", datetime.datetime.utcnow().isoformat(), 0)
            )
    conn_notif.commit()
    print("Seeded 20 notification history records.")

    conn_auth.close()
    conn_prof.close()
    conn_prop.close()
    conn_ag.close()
    conn_pay.close()
    conn_notif.close()
    
    print("Master Seed Complete! Use 'password123' to login.")

if __name__ == "__main__":
    seed()
