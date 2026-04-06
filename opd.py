
import streamlit as st

from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import os
import sqlite3

from doctor_master import DOCTOR_DATABASE
import pandas as pd

from opd_documentation import opd_documentation_panel
from supabase import create_client
from datetime import date


from datetime import date
from supabase_client import supabase


@st.cache_data(ttl=10)
def load_today_opd():

    today = str(date.today())

    result = supabase.table("opd_live")\
        .select("token,uhid,name,doctor,visit_type,status,date")\
        .eq("date", today)\
        .order("token")\
        .limit(100)\
        .execute()

    return result.data



# Get absolute project folder path





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











# ----------------------------------------
# DATABASE CONNECTION
# ----------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn





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

   

    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000)

    st.title("🏥 Live OPD Reception Control")

    

    today = str(datetime.now().date())

    # ===============================
    # 📊 LIVE METRICS
    # ===============================
    today = str(date.today())

    result = supabase.table("opd_live")\
        .select("token,uhid,name,doctor,visit_type,status,date")\
        .eq("date", today)\
        .order("token")\
        .limit(100)\
        .execute()

    rows = result.data

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

   

   

    today = str(date.today())

    result_all = supabase.table("opd_live")\
        .select("*")\
        .eq("date", today)\
        .execute()

    all_rows = result_all.data

    
    result_doc = supabase.table("opd_live")\
        .select("*")\
        .eq("doctor", doctor_name)\
        .eq("date", today)\
        .execute()

    rows = result_doc.data

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

                    supabase.table("opd_live")\
                    .update({
                        "status": "In Consultation",
                        "consult_start": str(datetime.now())
                    })\
                    .eq("id", r["id"])\
                    .execute()

                   
                    st.rerun()

        with col3:
            if r["status"] == "In Consultation":
                if st.button("✔ Complete", key=f"finish_{idx}"):

                    supabase.table("opd_live")\
                    .update({
                        "status": "Consulted",
                        "consult_end": str(datetime.now())
                    })\
                    .eq("id", r["id"])\
                    .execute()

                    st.rerun()

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

        supabase.table("opd_live")\
        .update({"status":"Consulted"})\
        .eq("doctor", doctor_name)\
        .eq("date", today)\
        .eq("status","Waiting")\
        .execute()

        st.success("All waiting patients marked as Consulted")

        st.rerun())

       








from doctor_master import DOCTOR_DATABASE
import pandas as pd

from opd_documentation import opd_documentation_panel


# Get absolute project folder path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create full absolute DB path
DB_PATH = os.path.join(BASE_DIR, "hospital.db")







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


    # ===============================
    # 📊 LIVE METRICS
    # ===============================
    rows = load_today_opd()

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
    all_rows = load_today_opd()

    rows = [r for r in all_rows if r["doctor"] == doctor_name]

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