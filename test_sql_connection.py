
import pyodbc

conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=.\\HIS;"
    "DATABASE=myhms;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

cursor.execute("""
SELECT TOP 5 id, PName, MobileNo, ODate, CreatedAt 
FROM tblOpd
ORDER BY id DESC
""")

rows = cursor.fetchall()

for row in rows:
    print(row)


import pyodbc

conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=.\\HIS;"
    "DATABASE=myhms;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

cursor.execute("""
SELECT TOP 5 id, PName, MobileNo, ODate, CreatedAt 
FROM tblOpd
ORDER BY id DESC
""")

rows = cursor.fetchall()

for row in rows:
    print(row)


conn.close()