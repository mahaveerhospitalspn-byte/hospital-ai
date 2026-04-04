
import pyodbc
import os
import time

SERVER = r'.\HIS'
DATABASE = 'myhms'
LAST_ID_FILE = "last_sync.txt"

def get_last_synced_id():
    if not os.path.exists(LAST_ID_FILE):
        return 0
    with open(LAST_ID_FILE, "r") as f:
        return int(f.read())

def update_last_synced_id(last_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(last_id))

def sync_opd():
    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
    )

    cursor = conn.cursor()

    last_id = get_last_synced_id()

    cursor.execute("""
        SELECT id, PName, MobileNo, ODate, CreatedAt
        FROM tblOpd
        WHERE id > ?
        ORDER BY id
    """, last_id)

    rows = cursor.fetchall()

    for row in rows:
        patient_id = row.id
        name = row.PName
        mobile = row.MobileNo
        date = row.ODate

        print("New Patient Found:", patient_id, name)

        # 👉 HERE you insert into your Hospital_AI database
        # save_patient_to_your_db(name, mobile, date)

        update_last_synced_id(patient_id)

    conn.close()

if __name__ == "__main__":
    while True:
        sync_opd()

import pyodbc
import os
import time

SERVER = r'.\HIS'
DATABASE = 'myhms'
LAST_ID_FILE = "last_sync.txt"

def get_last_synced_id():
    if not os.path.exists(LAST_ID_FILE):
        return 0
    with open(LAST_ID_FILE, "r") as f:
        return int(f.read())

def update_last_synced_id(last_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(last_id))

def sync_opd():
    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
    )

    cursor = conn.cursor()

    last_id = get_last_synced_id()

    cursor.execute("""
        SELECT id, PName, MobileNo, ODate, CreatedAt
        FROM tblOpd
        WHERE id > ?
        ORDER BY id
    """, last_id)

    rows = cursor.fetchall()

    for row in rows:
        patient_id = row.id
        name = row.PName
        mobile = row.MobileNo
        date = row.ODate

        print("New Patient Found:", patient_id, name)

        # 👉 HERE you insert into your Hospital_AI database
        # save_patient_to_your_db(name, mobile, date)

        update_last_synced_id(patient_id)

    conn.close()

if __name__ == "__main__":
    while True:
        sync_opd()

        time.sleep(10)  # check every 10 seconds