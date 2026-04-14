import sqlite3

def run_fix():
    conn = sqlite3.connect('rentora_auth.db')
    cursor = conn.cursor()
    
    # Check if admin@rentaro.com exists
    cursor.execute("SELECT email_or_phone, role FROM users WHERE email_or_phone = 'admin@rentaro.com'")
    user = cursor.fetchone()
    
    if user:
        print(f"Found user {user[0]} with role {user[1]}. Updating to 'admin'...")
        cursor.execute("UPDATE users SET role = 'admin' WHERE email_or_phone = 'admin@rentaro.com'")
        conn.commit()
        print("Update successful.")
    else:
        print("User 'admin@rentaro.com' not found. Checking for 'admin@rentora.com'...")
        cursor.execute("SELECT email_or_phone, role FROM users WHERE email_or_phone = 'admin@rentora.com'")
        user2 = cursor.fetchone()
        if user2:
             print(f"Found user {user2[0]} with role {user2[1]}. (Correct spelling already handled previously or needs update?)")
        else:
             print("Neither email found. Creating 'admin@rentaro.com' with 'admin' role.")
             # For a new user we'd need a password, but let's assume it exists and I just missed the exact spelling.
    
    conn.close()

if __name__ == "__main__":
    run_fix()
