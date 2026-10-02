import bcrypt
import sqlite3

def verify():
    h = '$2b$12$HPAKUM7oANhlfIgIO2N3iOLQD8SFrwF3EiLsJUpuZc/2HYEBmw1ym'
    p = 'password123'
    match = bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    print(f"Match: {match}")

    # Check database directly
    conn = sqlite3.connect('rentora_auth.db')
    cur = conn.cursor()
    cur.execute("SELECT hashed_password FROM users WHERE email_or_phone = 'admin@rentora.com'")
    row = cur.fetchone()
    if row:
        db_hash = row[0]
        db_match = bcrypt.checkpw(p.encode('utf-8'), db_hash.encode('utf-8'))
        print(f"DB Hash Match: {db_match}")
    else:
        print("User not found in DB")
    conn.close()

if __name__ == "__main__":
    verify()
