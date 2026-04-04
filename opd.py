
import streamlit as st
import sqlite3
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import os
import sqlite3
import streamlit as st
from datetime import datetime
from doctor_master import DOCTOR_DATABASE
import pandas as pd
import os
from opd_documentation import opd_documentation_panel


# Get absolute project folder path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create full absolute DB path
DB_PATH = os.path.join(BASE_DIR, "hospital.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def opd_reception_panel():
    st.title("🧾 OPD Reception Panel")

    st.subheader("👨‍⚕️ Select Doctor")

    doctor_display = [
        f"{name} ({data['degree']})"
        for name, data in DOCTOR_DATABASE.items()
    ]

    selected_display = st.selectbox(
        "Doctor Name",
        doctor_display
    )
    
    selected_doctor = selected_display.split(" (")[0]
    st.markdown("---")
    st.subheader("👤 Patient Entry")

    patient_name = st.text_input("Patient Name")
    age = st.text_input("Age")


    if st.button("💾 Register OPD Patient"):

        if patient_name.strip() == "":
            st.error("Patient Name Required")
        else:

            entry = {
                "Date": datetime.now().strftime("%d-%m-%Y"),
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Patient Name": patient_name,
                "Age": age,
                "Doctor": selected_doctor
            
            }

            os.makedirs("OPD_Records", exist_ok=True)

            file_path = "OPD_Records/OPD_Register.csv"

            df_entry = pd.DataFrame([entry])

            if os.path.exists(file_path):
                df_entry.to_csv(file_path, mode='a', header=False, index=False)
            else:
                df_entry.to_csv(file_path, index=False)

        st.success("✅ OPD Patient Registered")

def end_all_waiting_patients():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE opd
    SET status = 'Consulted'
    WHERE status = 'Waiting'
    """)

    conn.commit()
    conn.close()

    st.success("All waiting patients marked as Consulted")


def opd_doctor_panel():
    st.title("👨‍⚕️ OPD Doctor Panel")
    st.write("Doctor OPD module")








# ----------------------------------------
# DATABASE CONNECTION
# ----------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------------------
# CREATE TABLE (RUNS ONCE)
# ----------------------------------------
def create_opd_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opd_live (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token INTEGER,
            uhid TEXT,
            name TEXT,
            doctor TEXT,
            visit_type TEXT,
            arrival_time TEXT,
            status TEXT,
            procedure_done TEXT,
            consult_start TEXT,
            consult_end TEXT,
            date TEXT,
            UNIQUE(token, date)
        )
    """)

    conn.commit()
    conn.close()


# ----------------------------------------
# AUTO VISIT TYPE DETECTION
# ----------------------------------------
def detect_visit_type(uhid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM opd_live WHERE uhid = ?", (uhid,))
    count = cursor.fetchone()[0]

    conn.close()

    if count == 0:
        return "New"
    return "Revisit"


# ----------------------------------------
# GENERATE TOKEN
# ----------------------------------------
def generate_token():
    today = datetime.now().date()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(token) FROM opd_live WHERE date = ?", (str(today),))
    result = cursor.fetchone()[0]

    conn.close()

    if result is None:
        return 1
    return result + 1

def end_all_waiting_patients():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE opd_live
    SET status = 'Consulted'
    WHERE status = 'Waiting'
    """)

    conn.commit()
    conn.close()

    st.success("All waiting patients marked as Consulted")

# ----------------------------------------
# RECEPTION PANEL
# ----------------------------------------

# 🧾 LIVE OPD RECEPTION PANEL (CLEAN VERSION)

def opd_reception_panel():

    create_opd_table()

    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=4000)

    st.title("🏥 Live OPD Reception Control")

    conn = get_connection()
    cursor = conn.cursor()

    today = str(datetime.now().date())

    # ===============================
    # 📊 LIVE METRICS
    # ===============================
    cursor.execute("SELECT * FROM opd_live WHERE date = ?", (today,))
    rows = cursor.fetchall()

    total = len(rows)
    waiting = len([r for r in rows if r["status"] == "Waiting"])
    consulted = len([r for r in rows if r["status"] == "Consulted"])
    in_consult = len([r for r in rows if r["status"] == "In Consultation"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", total)
    col2.metric("Waiting", waiting)
    col3.metric("In Consultation", in_consult)
    col4.metric("Consulted", consulted)

    st.divider()

    # ===============================
    # ➕ ADD NEW OPD ENTRY
    # ===============================
    # ===============================
# 🔍 PATIENT SEARCH
# ===============================
    st.subheader("🔍 Search Patient")

    search_name = st.text_input("Type Patient Name")

    if search_name:

        cursor.execute("""
            SELECT uhid, name, date
            FROM opd_live
            WHERE name LIKE ?
            ORDER BY date DESC
            LIMIT 10
        """, (f"%{search_name}%",))

        results = cursor.fetchall()

        if results:

            st.write("Matching Patients:")

            for r in results:

                col1, col2, col3, col4 = st.columns([3,2,2,1])

                col1.write(r["name"])
                col2.write(r["uhid"])
                col3.write(r["date"])

                if col4.button("Select", key=f"pick_{r['uhid']}_{r['date']}"):

                    st.session_state.selected_uhid = r["uhid"]
                    st.rerun()
    

    st.subheader("➕ Register New OPD Patient")

    with st.form("opd_form", clear_on_submit=True):

        name = st.text_input("Patient Name")
        uhid = st.text_input(
            "UHID",
            value=st.session_state.get("selected_uhid",""),
            key="uhid_field"
        ) 
        
        doctor = st.selectbox(
            "Assign Doctor",
            [
                "DR SIDDHARTH RASTOGI",
                "DR RAJESH RASTOGI",
                "DR RUCHIKA RASTOGI"
            ]
        )

        submitted = st.form_submit_button("💾 Add to OPD")

        if submitted:

            if name.strip() == "" or uhid.strip() == "":
                st.error("Patient Name and UHID Required")

            else:

                token = generate_token()
                visit_type = detect_visit_type(uhid)

                cursor.execute("""
                    INSERT INTO opd_live 
                    (token, uhid, name, doctor, visit_type, arrival_time, status, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    token,
                    uhid.strip(),
                    name.strip(),
                    doctor,
                    visit_type,
                    str(datetime.now()),
                    "Waiting",
                    today
                ))

                conn.commit()

                st.success(f"🎟 Token {token} Generated Successfully")
                st.rerun()

    st.divider()

   

    



 # ===============================
    # 📋 LIVE QUEUE DISPLAY
    # ===============================
    st.subheader("📋 Live OPD Queue")
    
    if rows:

        for r in rows:
            st.write(
                f"🎟 {r['token']} | {r['name']} | "
                f"{r['doctor']} | {r['visit_type']} | {r['status']}"
            )
    else:
        st.info("No Patients Added Yet")

    conn.close()

# ----------------------------------------
# DOCTOR PANEL
# ----------------------------------------
...
# ----------------------------------------
# DOCTOR PANEL
# ----------------------------------------
def opd_doctor_panel(doctor_name):

    create_opd_table()

    conn = get_connection()
    cursor = conn.cursor()

    today = str(datetime.now().date())

    cursor.execute("SELECT * FROM opd_live WHERE date = ?", (today,))
    all_rows = cursor.fetchall()

    rows = cursor.fetchall()
    cursor.execute("""
        SELECT * FROM opd_live
        WHERE doctor = ? AND date = ?
    """, (doctor_name, today))

    rows = cursor.fetchall()

    # Row 1
    total_doctor = len(rows)
    waiting = len([r for r in rows if r["status"] == "Waiting"])
    consulted = len([r for r in rows if r["status"] == "Consulted"])
    new_patients = len([r for r in rows if r["visit_type"] == "New"])
    revisit_patients = len([r for r in rows if r["visit_type"] == "Revisit"])


    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total", total_doctor)
    col2.metric("Waiting", waiting)
    col3.metric("Consulted", consulted)
    col4.metric("New Patients", new_patients)
    col5.metric("Revisit", revisit_patients)

    st.divider()

    # Row 2
    total_hospital = len(all_rows)

    dr_rajesh = len([r for r in all_rows if r["doctor"] == "DR RAJESH RASTOGI"])
    dr_ruchika = len([r for r in all_rows if r["doctor"] == "DR RUCHIKA RASTOGI"])

    col4, col5, col6 = st.columns(3)

    col4.metric("Total OPD Today", total_hospital)
    col5.metric("Dr Rajesh Rastogi Patients", dr_rajesh)
    col6.metric("Dr Ruchika Rastogi Patients", dr_ruchika)
    # ===============================
    # TABLE DISPLAY ONLY
    # ===============================
    table_data = []

    for r in rows:
        queue = r["name"] if r["status"] == "Waiting" else ""
        consulted = r["name"] if r["status"] == "Consulted" else ""

        table_data.append({
            "Token": r["token"],
            "In Queue": queue,
            "Consulted": consulted,
            "Procedure": r["procedure_done"] or ""
        })

    import pandas as pd
    st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    # ===============================
    # OPD DOCTOR QUEUE
    # ===============================

    if "open_doc_id" not in st.session_state:
        st.session_state.open_doc_id = None

    for idx, r in enumerate(rows):

        st.markdown(f"### 👤 Token {r['token']} | {r['name']} | {r['status']}")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📝 Documentation", key=f"doc_{r['id']}"):
                st.session_state.open_doc_id = r["id"]

        with col2:
            if r["status"] == "Waiting":
                if st.button("▶ Start", key=f"start_{idx}"):

                    cursor.execute("""
                        UPDATE opd_live
                        SET status = ?, consult_start = ?
                        WHERE id = ?
                    """, ("In Consultation", str(datetime.now()), r["id"]))

                    conn.commit()
                    st.rerun()

        with col3:
            if r["status"] == "In Consultation":
                if st.button("✔ Complete", key=f"finish_{idx}"):

                    cursor.execute("""
                        UPDATE opd_live
                        SET status = ?, consult_end = ?
                        WHERE id = ?
                    """, ("Consulted", str(datetime.now()), r["id"]))

                    conn.commit()

                    st.session_state.open_doc_id = None
                    st.rerun()

        st.divider()

    # ===============================
    # DOCUMENTATION PANEL
    # ===============================

    if st.session_state.open_doc_id is not None:

        selected_row = None

        for row in rows:
            if row["id"] == st.session_state.open_doc_id:
                selected_row = row
                break

        if selected_row:
            with st.expander("📝 OPD Documentation", expanded=True):
                opd_documentation_panel(selected_row)

    

    st.markdown("---")
    st.subheader("🩺 Consultation Control")

    if st.button("End OPD - Mark All Waiting Consulted"):

        cursor.execute("""
            UPDATE opd_live
            SET status = 'Consulted'
            WHERE status = 'Waiting'
            AND doctor = ?
            AND date = ?
        """, (doctor_name, today))

        conn.commit()

        st.success("All waiting patients marked as Consulted")

import streamlit as st
import sqlite3
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import os
import sqlite3
import streamlit as st
from datetime import datetime
from doctor_master import DOCTOR_DATABASE
import pandas as pd
import os
from opd_documentation import opd_documentation_panel


# Get absolute project folder path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create full absolute DB path
DB_PATH = os.path.join(BASE_DIR, "hospital.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def opd_reception_panel():
    st.title("🧾 OPD Reception Panel")

    st.subheader("👨‍⚕️ Select Doctor")

    doctor_display = [
        f"{name} ({data['degree']})"
        for name, data in DOCTOR_DATABASE.items()
    ]

    selected_display = st.selectbox(
        "Doctor Name",
        doctor_display
    )
    
    selected_doctor = selected_display.split(" (")[0]
    st.markdown("---")
    st.subheader("👤 Patient Entry")

    patient_name = st.text_input("Patient Name")
    age = st.text_input("Age")


    if st.button("💾 Register OPD Patient"):

        if patient_name.strip() == "":
            st.error("Patient Name Required")
        else:

            entry = {
                "Date": datetime.now().strftime("%d-%m-%Y"),
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Patient Name": patient_name,
                "Age": age,
                "Doctor": selected_doctor
            
            }

            os.makedirs("OPD_Records", exist_ok=True)

            file_path = "OPD_Records/OPD_Register.csv"

            df_entry = pd.DataFrame([entry])

            if os.path.exists(file_path):
                df_entry.to_csv(file_path, mode='a', header=False, index=False)
            else:
                df_entry.to_csv(file_path, index=False)

        st.success("✅ OPD Patient Registered")

def end_all_waiting_patients():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE opd
    SET status = 'Consulted'
    WHERE status = 'Waiting'
    """)

    conn.commit()
    conn.close()

    st.success("All waiting patients marked as Consulted")


def opd_doctor_panel():
    st.title("👨‍⚕️ OPD Doctor Panel")
    st.write("Doctor OPD module")








# ----------------------------------------
# DATABASE CONNECTION
# ----------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------------------
# CREATE TABLE (RUNS ONCE)
# ----------------------------------------
def create_opd_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opd_live (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token INTEGER,
            uhid TEXT,
            name TEXT,
            doctor TEXT,
            visit_type TEXT,
            arrival_time TEXT,
            status TEXT,
            procedure_done TEXT,
            consult_start TEXT,
            consult_end TEXT,
            date TEXT,
            UNIQUE(token, date)
        )
    """)

    conn.commit()
    conn.close()


# ----------------------------------------
# AUTO VISIT TYPE DETECTION
# ----------------------------------------
def detect_visit_type(uhid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM opd_live WHERE uhid = ?", (uhid,))
    count = cursor.fetchone()[0]

    conn.close()

    if count == 0:
        return "New"
    return "Revisit"


# ----------------------------------------
# GENERATE TOKEN
# ----------------------------------------
def generate_token():
    today = datetime.now().date()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(token) FROM opd_live WHERE date = ?", (str(today),))
    result = cursor.fetchone()[0]

    conn.close()

    if result is None:
        return 1
    return result + 1

def end_all_waiting_patients():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE opd_live
    SET status = 'Consulted'
    WHERE status = 'Waiting'
    """)

    conn.commit()
    conn.close()

    st.success("All waiting patients marked as Consulted")

# ----------------------------------------
# RECEPTION PANEL
# ----------------------------------------
# =========================================================
# 🧾 LIVE OPD RECEPTION PANEL (CLEAN VERSION)
# =========================================================
def opd_reception_panel():

    create_opd_table()

    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=4000)

    st.title("🏥 Live OPD Reception Control")

    conn = get_connection()
    cursor = conn.cursor()

    today = str(datetime.now().date())

    # ===============================
    # 📊 LIVE METRICS
    # ===============================
    cursor.execute("SELECT * FROM opd_live WHERE date = ?", (today,))
    rows = cursor.fetchall()

    total = len(rows)
    waiting = len([r for r in rows if r["status"] == "Waiting"])
    consulted = len([r for r in rows if r["status"] == "Consulted"])
    in_consult = len([r for r in rows if r["status"] == "In Consultation"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", total)
    col2.metric("Waiting", waiting)
    col3.metric("In Consultation", in_consult)
    col4.metric("Consulted", consulted)

    st.divider()

    # ===============================
    # ➕ ADD NEW OPD ENTRY
    # ===============================
    # ===============================
# 🔍 PATIENT SEARCH
# ===============================
    st.subheader("🔍 Search Patient")

    search_name = st.text_input("Type Patient Name")

    if search_name:

        cursor.execute("""
            SELECT uhid, name, date
            FROM opd_live
            WHERE name LIKE ?
            ORDER BY date DESC
            LIMIT 10
        """, (f"%{search_name}%",))

        results = cursor.fetchall()

        if results:

            st.write("Matching Patients:")

            for r in results:

                col1, col2, col3, col4 = st.columns([3,2,2,1])

                col1.write(r["name"])
                col2.write(r["uhid"])
                col3.write(r["date"])

                if col4.button("Select", key=f"pick_{r['uhid']}_{r['date']}"):

                    st.session_state.selected_uhid = r["uhid"]
                    st.rerun()
    

    st.subheader("➕ Register New OPD Patient")

    with st.form("opd_form", clear_on_submit=True):

        name = st.text_input("Patient Name")
        uhid = st.text_input(
            "UHID",
            value=st.session_state.get("selected_uhid",""),
            key="uhid_field"
        ) 
        
        doctor = st.selectbox(
            "Assign Doctor",
            [
                "DR SIDDHARTH RASTOGI",
                "DR RAJESH RASTOGI",
                "DR RUCHIKA RASTOGI"
            ]
        )

        submitted = st.form_submit_button("💾 Add to OPD")

        if submitted:

            if name.strip() == "" or uhid.strip() == "":
                st.error("Patient Name and UHID Required")

            else:

                token = generate_token()
                visit_type = detect_visit_type(uhid)

                cursor.execute("""
                    INSERT INTO opd_live 
                    (token, uhid, name, doctor, visit_type, arrival_time, status, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    token,
                    uhid.strip(),
                    name.strip(),
                    doctor,
                    visit_type,
                    str(datetime.now()),
                    "Waiting",
                    today
                ))

                conn.commit()

                st.success(f"🎟 Token {token} Generated Successfully")
                st.rerun()

    st.divider()

   

    



 # ===============================
    # 📋 LIVE QUEUE DISPLAY
    # ===============================
    st.subheader("📋 Live OPD Queue")
    
    if rows:

        for r in rows:
            st.write(
                f"🎟 {r['token']} | {r['name']} | "
                f"{r['doctor']} | {r['visit_type']} | {r['status']}"
            )
    else:
        st.info("No Patients Added Yet")

    conn.close()

# ----------------------------------------
# DOCTOR PANEL
# ----------------------------------------
...
# ----------------------------------------
# DOCTOR PANEL
# ----------------------------------------
def opd_doctor_panel(doctor_name):

    create_opd_table()

    conn = get_connection()
    cursor = conn.cursor()

    today = str(datetime.now().date())

    cursor.execute("SELECT * FROM opd_live WHERE date = ?", (today,))
    all_rows = cursor.fetchall()

    rows = cursor.fetchall()
    cursor.execute("""
        SELECT * FROM opd_live
        WHERE doctor = ? AND date = ?
    """, (doctor_name, today))

    rows = cursor.fetchall()

    # Row 1
    total_doctor = len(rows)
    waiting = len([r for r in rows if r["status"] == "Waiting"])
    consulted = len([r for r in rows if r["status"] == "Consulted"])
    new_patients = len([r for r in rows if r["visit_type"] == "New"])
    revisit_patients = len([r for r in rows if r["visit_type"] == "Revisit"])


    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total", total_doctor)
    col2.metric("Waiting", waiting)
    col3.metric("Consulted", consulted)
    col4.metric("New Patients", new_patients)
    col5.metric("Revisit", revisit_patients)

    st.divider()

    # Row 2
    total_hospital = len(all_rows)

    dr_rajesh = len([r for r in all_rows if r["doctor"] == "DR RAJESH RASTOGI"])
    dr_ruchika = len([r for r in all_rows if r["doctor"] == "DR RUCHIKA RASTOGI"])

    col4, col5, col6 = st.columns(3)

    col4.metric("Total OPD Today", total_hospital)
    col5.metric("Dr Rajesh Rastogi Patients", dr_rajesh)
    col6.metric("Dr Ruchika Rastogi Patients", dr_ruchika)
    # ===============================
    # TABLE DISPLAY ONLY
    # ===============================
    table_data = []

    for r in rows:
        queue = r["name"] if r["status"] == "Waiting" else ""
        consulted = r["name"] if r["status"] == "Consulted" else ""

        table_data.append({
            "Token": r["token"],
            "In Queue": queue,
            "Consulted": consulted,
            "Procedure": r["procedure_done"] or ""
        })

    import pandas as pd
    st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    # ===============================
    # OPD DOCTOR QUEUE
    # ===============================

    if "open_doc_id" not in st.session_state:
        st.session_state.open_doc_id = None

    for idx, r in enumerate(rows):

        st.markdown(f"### 👤 Token {r['token']} | {r['name']} | {r['status']}")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📝 Documentation", key=f"doc_{r['id']}"):
                st.session_state.open_doc_id = r["id"]

        with col2:
            if r["status"] == "Waiting":
                if st.button("▶ Start", key=f"start_{idx}"):

                    cursor.execute("""
                        UPDATE opd_live
                        SET status = ?, consult_start = ?
                        WHERE id = ?
                    """, ("In Consultation", str(datetime.now()), r["id"]))

                    conn.commit()
                    st.rerun()

        with col3:
            if r["status"] == "In Consultation":
                if st.button("✔ Complete", key=f"finish_{idx}"):

                    cursor.execute("""
                        UPDATE opd_live
                        SET status = ?, consult_end = ?
                        WHERE id = ?
                    """, ("Consulted", str(datetime.now()), r["id"]))

                    conn.commit()

                    st.session_state.open_doc_id = None
                    st.rerun()

        st.divider()

    # ===============================
    # DOCUMENTATION PANEL
    # ===============================

    if st.session_state.open_doc_id is not None:

        selected_row = None

        for row in rows:
            if row["id"] == st.session_state.open_doc_id:
                selected_row = row
                break

        if selected_row:
            with st.expander("📝 OPD Documentation", expanded=True):
                opd_documentation_panel(selected_row)

    

    st.markdown("---")
    st.subheader("🩺 Consultation Control")

    if st.button("End OPD - Mark All Waiting Consulted"):

        cursor.execute("""
            UPDATE opd_live
            SET status = 'Consulted'
            WHERE status = 'Waiting'
            AND doctor = ?
            AND date = ?
        """, (doctor_name, today))

        conn.commit()

        st.success("All waiting patients marked as Consulted")

        st.rerun()