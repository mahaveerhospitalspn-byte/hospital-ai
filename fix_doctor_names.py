
import sqlite3

conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

cursor.execute("""
UPDATE opd_live
SET doctor = 'DR SIDDHARTH RASTOGI'
WHERE doctor LIKE '%SIDDHARTH%'
""")

conn.commit()
conn.close()


import sqlite3

conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

cursor.execute("""
UPDATE opd_live
SET doctor = 'DR SIDDHARTH RASTOGI'
WHERE doctor LIKE '%SIDDHARTH%'
""")

conn.commit()
conn.close()

print("Doctor names normalized successfully")