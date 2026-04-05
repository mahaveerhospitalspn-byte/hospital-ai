import pyodbc
import requests
import time

SUPABASE_URL = "https://ptkdegqftfcaqrvsbihk.supabase.co"

SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0a2RlZ3FmdGZjYXFydnNiaWhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxMjYzODUsImV4cCI6MjA5MDcwMjM4NX0.jI2mcxJ86uPaCExOmLEdN8XdEzctEul3-33Qc7Ug_dI"

SERVER = r'.\HIS'
DATABASE = 'myhms'

LAST_ID_FILE = "last_sync.txt"


def get_last_id():
    try:
        with open(LAST_ID_FILE) as f:
            return int(f.read())
    except:
        return 0


def save_last_id(i):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(i))


def sync():

    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
    )

    cursor = conn.cursor()

    last_id = get_last_id()

    cursor.execute("""
        SELECT 
            o.id,
            o.UHID,
            o.PName,
            o.VisitNo,
            o.ODate,
            o.OTime,
            c.Descript
        FROM tblOpd o
        JOIN tblConsultant c ON o.DocId = c.id
        WHERE o.id > ?
        ORDER BY o.id
    """, last_id)

    rows = cursor.fetchall()

    for r in rows:

        data = {
            "token": str(r.VisitNo),
            "uhid": str(r.UHID),
            "name": r.PName,
            "doctor": r.Descript.upper(),
            "visit_type": "Normal",
            "arrival_time": str(r.OTime),
            "status": "Waiting",
            "date": str(r.ODate)
        }

        requests.post(
            SUPABASE_URL,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            },
            json=data
        )

        save_last_id(r.id)

        print("Synced:", r.PName)

    conn.close()


while True:

    try:

        sync()

        time.sleep(5)

    except Exception as e:

        print("ERROR", e)

        time.sleep(10)