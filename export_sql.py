import pyodbc
import pandas as pd

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=MYHMS;"
    "Trusted_Connection=yes;"
)

df = pd.read_sql("SELECT TOP 20 * FROM Patient", conn)

print(df.head())

df.to_csv("patient_export.csv", index=False)

conn.close()

print("Export complete")