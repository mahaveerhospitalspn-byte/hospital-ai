<<<<<<< HEAD
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

=======
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

>>>>>>> d67240b6b301f5efd6ea7b3a00d8b3b998948d69
print("Doctor names normalized successfully")