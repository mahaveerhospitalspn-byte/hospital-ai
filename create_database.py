<<<<<<< HEAD
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

=======
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

>>>>>>> d67240b6b301f5efd6ea7b3a00d8b3b998948d69
print("Database created successfully")