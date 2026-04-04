
import streamlit as st
from datetime import datetime
import sqlite3
import os
import pandas as pd

# Use same DB as opd.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hospital.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_drug_master():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drug_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        salt TEXT,
        strength TEXT,
        manufacturer TEXT,
        price TEXT
    )
    """)

    conn.commit()
    conn.close()



def import_large_drug_dataset():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM drug_master")
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        return

    csv_file = os.path.join(BASE_DIR, "indian_medicine_data.csv")

    if os.path.exists(csv_file):

        df = pd.read_csv(csv_file)

        for _, row in df.iterrows():

            brand = str(row["brand_name"])
            salt = str(row["primary_ingredient"])
            strength = str(row["primary_strength"])
            manufacturer = str(row["manufacturer"])
            price = str(row["price_inr"])

            cursor.execute("""
            INSERT INTO drug_master
            (brand, salt, strength, manufacturer, price)
            VALUES (?, ?, ?, ?, ?)
            """, (brand, salt, strength, manufacturer, price))

        conn.commit()

    conn.close()


def create_prescription_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opd_id INTEGER,
        uhid TEXT,
        drug TEXT,
        dose TEXT,
        days INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()



# ----------------------------------------
# CREATE OPD NOTES TABLE
# ----------------------------------------
def create_opd_notes_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opd_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opd_id INTEGER,
            uhid TEXT,
            doctor TEXT,
            chief_complaint TEXT,
            history TEXT,
            examination TEXT,
            diagnosis TEXT,
            prescription TEXT,
            advice TEXT,
            follow_up TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def load_default_drugs():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM drug_master")
    count = cursor.fetchone()[0]

    if count == 0:

        default_drugs = [
            ("Paracetamol",),
            ("Amoxicillin",),
            ("Azithromycin",),
            ("Cefixime",),
            ("Pantoprazole",),
            ("Rabeprazole",),
            ("Diclofenac",),
            ("Aceclofenac",),
            ("Metformin",),
            ("Amlodipine",)
        ]

        cursor.executemany(
            "INSERT OR IGNORE INTO drug_master (drug_name) VALUES (?)",
            default_drugs
        )

    conn.commit()
    conn.close()


import pandas as pd

def import_drugs_from_csv():

    conn = get_connection()
    cursor = conn.cursor()

    csv_file = os.path.join(BASE_DIR, "drug_master.csv")

    if os.path.exists(csv_file):

        # Check if table already has data
        cursor.execute("SELECT COUNT(*) FROM drug_master")
        count = cursor.fetchone()[0]

        if count == 0:

            df = pd.read_csv(csv_file)

            for drug in df["drug_name"]:
                cursor.execute(
                    "INSERT OR IGNORE INTO drug_master (drug_name) VALUES (?)",
                    (drug,)
                )

            conn.commit()

    conn.close()



# ----------------------------------------
# OPD DOCUMENTATION PANEL
# ----------------------------------------
def opd_documentation_panel(opd_row):

    create_opd_notes_table()
    create_prescription_table()
    


    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM opd_notes WHERE opd_id = ?",
        (opd_row["id"],)
    )

    existing_note = cursor.fetchone()
    conn.close()    

    st.title("📝 OPD Clinical Documentation")

    st.markdown(f"### 👤 Patient: {opd_row['name']}")
    st.write(f"UHID: {opd_row['uhid']}")
    st.write(f"Doctor: {opd_row['doctor']}")

    st.divider()

    chief_complaint = st.text_input("Chief Complaint")
    history = st.text_area("History")
    examination = st.text_area("Examination")
    diagnosis = st.text_input("Diagnosis")

    st.markdown("### 💊 Prescription")

    prescription = st.text_area(
        "Prescription",
        value=existing_note["prescription"] if existing_note else ""
    )

    advice = st.text_area(
        "Advice",
        value=existing_note["advice"] if existing_note else ""
    )

    follow_up = st.selectbox(
        "Follow Up",
        [
            "",
            "1 day",
            "2 day",
            "3 days",
            "5 days",
            "7 days",
            "10 days",
            "2 weeks",
           "1 month"
        ],
        index=0
    )
    
     

 # -------------------------
# MEDICINE ENTRY SYSTEM
# -------------------------

    search = st.text_input("🔍 Search Drug")

    conn = get_connection()
    cursor = conn.cursor()

    if search.strip() == "":
        cursor.execute("""
        SELECT brand || ' (' || salt || ' ' || strength || ')'
        FROM drug_master
        ORDER BY RANDOM()
        LIMIT 50
        """)
    else:
        cursor.execute("""
        SELECT brand || ' (' || salt || ' ' || strength || ')'
        FROM drug_master
        WHERE brand LIKE ? OR salt LIKE ?
        ORDER BY brand
        LIMIT 50
        """, (f"%{search}%", f"%{search}%"))

    drug_rows = cursor.fetchall()

    drug_list = [r[0] for r in drug_rows]

    conn.close()

    if "prescription_list" not in st.session_state:
        st.session_state.prescription_list = []

    col1, col2, col3, col4 = st.columns(4)

    drug_options = drug_list + ["➕ Add New Drug"]

    with col1:
        drug = st.selectbox(
            "Drug",
            drug_options,
            key=f"drug_{opd_row['id']}"
        )

    if drug == "➕ Add New Drug":
        drug = st.text_input("Enter New Drug Name")

    with col2:
        dose = st.selectbox(
            "Dose",
            ["1-0-1","1-0-0","0-1-0","0-0-1","1/2-0-1/2","1-1-1","SOS"],
            key=f"dose_{opd_row['id']}"
        )

    with col3:
        days = st.number_input(
            "Days",
            min_value=1,
            max_value=30,
            step=1,
            key=f"days_{opd_row['id']}"
        )

    with col4:
        if st.button("➕ Add", key=f"add_{opd_row['id']}"):

            if drug.strip() != "":

                st.session_state.prescription_list.append(
                    f"{drug}   {dose}   {days} days"
                )
    
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO prescriptions
                (opd_id, uhid, drug, dose, days, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    opd_row["id"],
                    opd_row["uhid"],
                    drug,
                    dose,
                    days,
                    str(datetime.now())
                ))

                conn.commit()
                conn.close()

            # Save new drug to SQLite database
                if drug not in drug_list:

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute(
                        "INSERT OR IGNORE INTO drug_master (drug_name) VALUES (?)",
                        (drug,)
                    )

                    conn.commit()
                    conn.close()

                st.success("Medicine Added")

        

    if st.session_state.prescription_list:

        st.markdown("### Added Medicines")

        for i, med in enumerate(st.session_state.prescription_list):

            col1, col2 = st.columns([6,1])

            col1.write(med)

            if col2.button("❌", key=f"remove_{i}"):
                st.session_state.prescription_list.pop(i)
                st.rerun()   

    
    prescription = "\n".join(st.session_state.prescription_list)

    if st.button("💾 Save Clinical Note"):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO opd_notes
            (opd_id, uhid, doctor, chief_complaint,
             history, examination, diagnosis,
             prescription, advice, follow_up, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opd_row["id"],
            opd_row["uhid"],
            opd_row["doctor"],
            chief_complaint,
            history,
            examination,
            diagnosis,
            prescription,
            advice,
            follow_up,
            str(datetime.now())
        ))

        conn.commit()
        conn.close()

        st.success("Clinical Note Saved Successfully")

import streamlit as st
from datetime import datetime
import sqlite3
import os
import pandas as pd

# Use same DB as opd.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hospital.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_drug_master():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drug_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        salt TEXT,
        strength TEXT,
        manufacturer TEXT,
        price TEXT
    )
    """)

    conn.commit()
    conn.close()



def import_large_drug_dataset():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM drug_master")
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        return

    csv_file = os.path.join(BASE_DIR, "indian_medicine_data.csv")

    if os.path.exists(csv_file):

        df = pd.read_csv(csv_file)

        for _, row in df.iterrows():

            brand = str(row["brand_name"])
            salt = str(row["primary_ingredient"])
            strength = str(row["primary_strength"])
            manufacturer = str(row["manufacturer"])
            price = str(row["price_inr"])

            cursor.execute("""
            INSERT INTO drug_master
            (brand, salt, strength, manufacturer, price)
            VALUES (?, ?, ?, ?, ?)
            """, (brand, salt, strength, manufacturer, price))

        conn.commit()

    conn.close()


def create_prescription_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opd_id INTEGER,
        uhid TEXT,
        drug TEXT,
        dose TEXT,
        days INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()



# ----------------------------------------
# CREATE OPD NOTES TABLE
# ----------------------------------------
def create_opd_notes_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opd_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opd_id INTEGER,
            uhid TEXT,
            doctor TEXT,
            chief_complaint TEXT,
            history TEXT,
            examination TEXT,
            diagnosis TEXT,
            prescription TEXT,
            advice TEXT,
            follow_up TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def load_default_drugs():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM drug_master")
    count = cursor.fetchone()[0]

    if count == 0:

        default_drugs = [
            ("Paracetamol",),
            ("Amoxicillin",),
            ("Azithromycin",),
            ("Cefixime",),
            ("Pantoprazole",),
            ("Rabeprazole",),
            ("Diclofenac",),
            ("Aceclofenac",),
            ("Metformin",),
            ("Amlodipine",)
        ]

        cursor.executemany(
            "INSERT OR IGNORE INTO drug_master (drug_name) VALUES (?)",
            default_drugs
        )

    conn.commit()
    conn.close()


import pandas as pd

def import_drugs_from_csv():

    conn = get_connection()
    cursor = conn.cursor()

    csv_file = os.path.join(BASE_DIR, "drug_master.csv")

    if os.path.exists(csv_file):

        # Check if table already has data
        cursor.execute("SELECT COUNT(*) FROM drug_master")
        count = cursor.fetchone()[0]

        if count == 0:

            df = pd.read_csv(csv_file)

            for drug in df["drug_name"]:
                cursor.execute(
                    "INSERT OR IGNORE INTO drug_master (drug_name) VALUES (?)",
                    (drug,)
                )

            conn.commit()

    conn.close()



# ----------------------------------------
# OPD DOCUMENTATION PANEL
# ----------------------------------------
def opd_documentation_panel(opd_row):

    create_opd_notes_table()
    create_prescription_table()
    


    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM opd_notes WHERE opd_id = ?",
        (opd_row["id"],)
    )

    existing_note = cursor.fetchone()
    conn.close()    

    st.title("📝 OPD Clinical Documentation")

    st.markdown(f"### 👤 Patient: {opd_row['name']}")
    st.write(f"UHID: {opd_row['uhid']}")
    st.write(f"Doctor: {opd_row['doctor']}")

    st.divider()

    chief_complaint = st.text_input("Chief Complaint")
    history = st.text_area("History")
    examination = st.text_area("Examination")
    diagnosis = st.text_input("Diagnosis")

    st.markdown("### 💊 Prescription")

    prescription = st.text_area(
        "Prescription",
        value=existing_note["prescription"] if existing_note else ""
    )

    advice = st.text_area(
        "Advice",
        value=existing_note["advice"] if existing_note else ""
    )

    follow_up = st.selectbox(
        "Follow Up",
        [
            "",
            "1 day",
            "2 day",
            "3 days",
            "5 days",
            "7 days",
            "10 days",
            "2 weeks",
           "1 month"
        ],
        index=0
    )
    
     

 # -------------------------
# MEDICINE ENTRY SYSTEM
# -------------------------

    search = st.text_input("🔍 Search Drug")

    conn = get_connection()
    cursor = conn.cursor()

    if search.strip() == "":
        cursor.execute("""
        SELECT brand || ' (' || salt || ' ' || strength || ')'
        FROM drug_master
        ORDER BY RANDOM()
        LIMIT 50
        """)
    else:
        cursor.execute("""
        SELECT brand || ' (' || salt || ' ' || strength || ')'
        FROM drug_master
        WHERE brand LIKE ? OR salt LIKE ?
        ORDER BY brand
        LIMIT 50
        """, (f"%{search}%", f"%{search}%"))

    drug_rows = cursor.fetchall()

    drug_list = [r[0] for r in drug_rows]

    conn.close()

    if "prescription_list" not in st.session_state:
        st.session_state.prescription_list = []

    col1, col2, col3, col4 = st.columns(4)

    drug_options = drug_list + ["➕ Add New Drug"]

    with col1:
        drug = st.selectbox(
            "Drug",
            drug_options,
            key=f"drug_{opd_row['id']}"
        )

    if drug == "➕ Add New Drug":
        drug = st.text_input("Enter New Drug Name")

    with col2:
        dose = st.selectbox(
            "Dose",
            ["1-0-1","1-0-0","0-1-0","0-0-1","1/2-0-1/2","1-1-1","SOS"],
            key=f"dose_{opd_row['id']}"
        )

    with col3:
        days = st.number_input(
            "Days",
            min_value=1,
            max_value=30,
            step=1,
            key=f"days_{opd_row['id']}"
        )

    with col4:
        if st.button("➕ Add", key=f"add_{opd_row['id']}"):

            if drug.strip() != "":

                st.session_state.prescription_list.append(
                    f"{drug}   {dose}   {days} days"
                )
    
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO prescriptions
                (opd_id, uhid, drug, dose, days, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    opd_row["id"],
                    opd_row["uhid"],
                    drug,
                    dose,
                    days,
                    str(datetime.now())
                ))

                conn.commit()
                conn.close()

            # Save new drug to SQLite database
                if drug not in drug_list:

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute(
                        "INSERT OR IGNORE INTO drug_master (drug_name) VALUES (?)",
                        (drug,)
                    )

                    conn.commit()
                    conn.close()

                st.success("Medicine Added")

        

    if st.session_state.prescription_list:

        st.markdown("### Added Medicines")

        for i, med in enumerate(st.session_state.prescription_list):

            col1, col2 = st.columns([6,1])

            col1.write(med)

            if col2.button("❌", key=f"remove_{i}"):
                st.session_state.prescription_list.pop(i)
                st.rerun()   

    
    prescription = "\n".join(st.session_state.prescription_list)

    if st.button("💾 Save Clinical Note"):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO opd_notes
            (opd_id, uhid, doctor, chief_complaint,
             history, examination, diagnosis,
             prescription, advice, follow_up, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opd_row["id"],
            opd_row["uhid"],
            opd_row["doctor"],
            chief_complaint,
            history,
            examination,
            diagnosis,
            prescription,
            advice,
            follow_up,
            str(datetime.now())
        ))

        conn.commit()
        conn.close()

        st.success("Clinical Note Saved Successfully")

        st.session_state.prescription_list = []