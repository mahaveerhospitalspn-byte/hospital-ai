import pyodbc
import requests
import time

SUPABASE_URL="https://ptkdegqftfcaqrvsbihk.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0a2RlZ3FmdGZjYXFydnNiaWhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxMjYzODUsImV4cCI6MjA5MDcwMjM4NX0.jI2mcxJ86uPaCExOmLEdN8XdEzctEul3-33Qc7Ug_dI"

SERVER=r'.\HIS'
DATABASE='myhms'

def sync():

    conn = pyodbc.connect(
        r"Driver={SQL Server};"
        r"Server=localhost\HIS;"
        r"Database=myhms;"
        r"Trusted_Connection=yes;"
    )

    cursor = conn.cursor()

    cursor.execute("""

    SELECT

    o.id,
    o.VisitNo,
    o.PName,
    o.ODate,
    o.OTime,
    o.UHID,

    c.Descript as doctor_name

    FROM tblOpd o

    LEFT JOIN tblConsultant c
    ON o.DocId = c.id

    WHERE CAST(o.ODate as date) = CAST(GETDATE() as date)

    ORDER BY o.id DESC

    """)

    rows = cursor.fetchall()

    for r in rows:
        print("FOUND:", r.PName)
        data = {

            "token": str(r.VisitNo),
            "uhid": str(r.UHID),
            "name": r.PName,
            "doctor": str(r.doctor_name).upper() if r.doctor_name else "GENERAL",
            "visit_type": "Normal",
            "arrival_time": str(r.OTime),
            "status": "Waiting",
            "date": str(r.ODate)

        }

        response = requests.post(

            f"{SUPABASE_URL}/rest/v1/opd_live",

            headers={

                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer":"return=minimal"

            },

            json=data
        )

        print("Synced:", r.PName, response.status_code)

    conn.close()


while True:

    try:

        sync()

        time.sleep(10)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(10)