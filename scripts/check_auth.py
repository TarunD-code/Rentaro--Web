import sqlite3

def check_db():
    conn = sqlite3.connect('rentora_auth.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    if ('users',) in tables:
        cursor.execute("PRAGMA table_info(users)")
        cols = cursor.fetchall()
        print(f"Users Columns: {[c[1] for c in cols]}")
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print(f"Users: {users}")
    
    conn.close()

if __name__ == "__main__":
    check_db()
