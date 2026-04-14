import sqlite3
conn = sqlite3.connect('rentora_auth.db')
cursor = conn.cursor()
cursor.execute("UPDATE users SET role='admin' WHERE email_or_phone='admin@rentora.com'")
conn.commit()
print('Rows updated:', cursor.rowcount)
conn.close()
