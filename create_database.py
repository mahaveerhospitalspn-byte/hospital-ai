
import sqlite3

conn = sqlite3.connect("local.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS patients(
id INTEGER PRIMARY KEY,
name TEXT,
age INTEGER,
mobile TEXT,
synced INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()
print("Database created successfully")
