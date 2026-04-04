
#import pyodbc
import sqlite3
import os
import time

# SQL SERVER (HIS)
SERVER = r'.\HIS'
DATABASE = 'myhms'

# SQLITE (FULL PATH IMPORTANT)
SQLITE_DB = r"C:\Users\admin\Desktop\Hospital_AI\hospital.db"

LAST_ID_FILE = "last_sync.txt"


def get_last_synced_id():
    if not os.path.exists(LAST_ID_FILE):
        return 0
    with open(LAST_ID_FILE, "r") as f:
        return int(f.read())


def update_last_synced_id(last_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(last_id))


def sync_data():

    # Connect to HIS
    sql_conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
    )
    sql_cursor = sql_conn.cursor()

    last_id = get_last_synced_id()

    sql_cursor.execute("""
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

    rows = sql_cursor.fetchall()

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    for row in rows:

        patient_id = row.id
        uhid = str(row.UHID)
        name = row.PName
        token = row.VisitNo
        date = str(row.ODate)
        arrival_time = str(row.OTime)
        doctor_name = row.Descript.strip().upper()

        print("Importing:", name)

        # ✅ INSERT WITH SOURCE = RECEPTION
        sqlite_cursor.execute("""
        INSERT INTO opd_live
        (token, uhid, name, doctor, visit_type, arrival_time, status, procedure_done, consult_start, consult_end, date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            token,
            uhid,
            name,
            doctor_name,
            "Normal",
            arrival_time,
            "Waiting",
            "",
            "",
            "",
            date,
            "RECEPTION"
        ))

        update_last_synced_id(patient_id)

    sqlite_conn.commit()
    sqlite_conn.close()
    sql_conn.close()


# ============================
# RUN LOOP
# ============================

if __name__ == "__main__":

    print("HIS Sync Started...")

    while True:
        try:
            sync_data()
            time.sleep(5)
        except Exception as e:
            print("Error:", e)

#import pyodbc
import sqlite3
import os
import time

# SQL SERVER (HIS)
SERVER = r'.\HIS'
DATABASE = 'myhms'

# SQLITE (FULL PATH IMPORTANT)
SQLITE_DB = r"C:\Users\admin\Desktop\Hospital_AI\hospital.db"

LAST_ID_FILE = "last_sync.txt"


def get_last_synced_id():
    if not os.path.exists(LAST_ID_FILE):
        return 0
    with open(LAST_ID_FILE, "r") as f:
        return int(f.read())


def update_last_synced_id(last_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(last_id))


def sync_data():

    # Connect to HIS
    sql_conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
    )
    sql_cursor = sql_conn.cursor()

    last_id = get_last_synced_id()

    sql_cursor.execute("""
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

    rows = sql_cursor.fetchall()

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    for row in rows:

        patient_id = row.id
        uhid = str(row.UHID)
        name = row.PName
        token = row.VisitNo
        date = str(row.ODate)
        arrival_time = str(row.OTime)
        doctor_name = row.Descript.strip().upper()

        print("Importing:", name)

        # ✅ INSERT WITH SOURCE = RECEPTION
        sqlite_cursor.execute("""
        INSERT INTO opd_live
        (token, uhid, name, doctor, visit_type, arrival_time, status, procedure_done, consult_start, consult_end, date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            token,
            uhid,
            name,
            doctor_name,
            "Normal",
            arrival_time,
            "Waiting",
            "",
            "",
            "",
            date,
            "RECEPTION"
        ))

        update_last_synced_id(patient_id)

    sqlite_conn.commit()
    sqlite_conn.close()
    sql_conn.close()


# ============================
# RUN LOOP
# ============================

if __name__ == "__main__":

    print("HIS Sync Started...")

    while True:
        try:
            sync_data()
            time.sleep(5)
        except Exception as e:
            print("Error:", e)

            time.sleep(15)