import sqlite3, os

os.makedirs("db", exist_ok=True)
conn = sqlite3.connect("db/users.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))

conn.commit()
conn.close()
print("Database initialized with user admin/admin123")
