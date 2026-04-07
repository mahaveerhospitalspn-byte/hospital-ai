import pyodbc

conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=.\\HIS;"
    "DATABASE=myhms;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

cursor.execute("SELECT TOP 5 * FROM tblOpd")

rows = cursor.fetchall()

for r in rows:
    print(r)

conn.close()