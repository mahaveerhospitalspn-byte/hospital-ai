import streamlit as st
import os
import pandas as pd
import csv
import base64
import zipfile
import shutil
import requests
import random
import threading
import time
import sqlite3
from datetime import datetime, timedelta

# ── Page config — MUST be the very first Streamlit call ──────────────────────
st.set_page_config(
    page_title="Mahaveer Hospital Clinical AI",
    page_icon="🏥",
    layout="wide"
)

# ── Module imports ────────────────────────────────────────────────────────────
from hospital_summary import generate_hospital_summary
from pharmacy_module import pharmacy_dashboard
from opd import opd_reception_panel, opd_doctor_panel
from ot_ai_app import ot_module
from opd_documentation import create_drug_master, import_large_drug_dataset
from supabase import create_client
from supabase_storage import (
    register_patient_sb, load_patient_info_sb, load_patient_name_sb,
    load_patient_status_sb, discharge_patient_sb, reverse_discharge_sb,
    get_admitted_patients_sb, patient_exists_sb, load_patient_registry_sb,
    save_vitals_sb, load_vitals_sb, vitals_done_today_sb,
    save_medication_sb, load_medications_sb, meds_done_today_sb,
    save_nursing_note_sb, load_nursing_notes_sb,
    save_ot_note_sb, load_ot_note_sb, ot_done_sb,
    save_diagnosis_sb, load_latest_diagnosis_sb,
    save_ot_register_sb, load_ot_register_sb,
    save_daycare_sb, load_daycare_register_sb,
    save_blood_product_sb, load_blood_products_sb,
    log_audit_sb, add_notification_sb, get_unseen_notifications_sb,
    request_summary_approval_sb, check_summary_status_sb, approve_summary_sb,
    load_users_sb, approve_user_sb, save_user_sb,
)
from streamlit_autorefresh import st_autorefresh

# ── Supabase client ───────────────────────────────────────────────────────────
import os as _os
SUPABASE_URL = _os.environ.get(
    "SUPABASE_URL",
    "https://ptkdegqftfcaqrvsbihk.supabase.co"
)
SUPABASE_KEY = _os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0a2RlZ3FmdGZjYXFydnNiaWhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxMjYzODUsImV4cCI6MjA5MDcwMjM4NX0.jI2mcxJ86uPaCExOmLEdN8XdEzctEul3-33Qc7Ug_dI"
)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Session state defaults ────────────────────────────────────────────────────
for _key, _val in {
    "logged_in":        False,
    "page":             "login",
    "selected_patient": "",
    "role":             "",
    "user":             "",
    "splash_done":      True,   # skip splash — causes blank screen on cloud
}.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val

# ── One-time startup (cached — never reruns) ──────────────────────────────────
@st.cache_resource(show_spinner=False)
def _startup_init():
    try:
        create_drug_master()
        import_large_drug_dataset()
    except Exception:
        pass  # Non-fatal if drug CSV not present on cloud

_startup_init()


def rebuild_registry_from_records():
    registry = "Patients_Data.csv"
    records_path = "Records"

    if not os.path.exists(records_path):
        return

    # ✅ LOAD EXISTING CSV FIRST
    if os.path.exists(registry) and os.path.getsize(registry) > 0:

        try:
            df_existing = pd.read_csv(registry, on_bad_lines='skip')
            df_existing["UHID"] = df_existing["UHID"].astype(str).str.strip()

        except:
            df_existing = pd.DataFrame(columns=["UHID", "Name", "Diagnosis", "Status"])

    else:
        df_existing = pd.DataFrame(columns=["UHID", "Name", "Diagnosis", "Status"])

    rows = []

    for uhid in os.listdir(records_path):

        info_file = f"{records_path}/{uhid}/Patient_Info.txt"

        if os.path.exists(info_file):

            with open(info_file, "r", encoding="utf-8") as f:

                lines = f.readlines()

                name = "Unknown"
                diagnosis = "General Case"

                for line in lines:

                    if "Name:" in line:
                        name = line.replace("Name:", "").strip()

                    if "Diagnosis:" in line:
                        diagnosis = line.replace("Diagnosis:", "").strip()

                # ✅ PRESERVE STATUS IF EXISTS
                existing_row = df_existing[df_existing["UHID"] == str(uhid)]

                if not existing_row.empty:
                    status = existing_row.iloc[0]["Status"]
                else:
                    status = "Admitted"

                rows.append({
                    "UHID": str(uhid),
                    "Name": name,
                    "Diagnosis": diagnosis,
                    "Status": status,
                    "Admitted_On": ""
                })

    df = pd.DataFrame(rows, columns=[
        "UHID",
        "Name",
        "Diagnosis",
        "Status",
        "Admitted_On"
    ])

    df.to_csv(registry, index=False)



rebuild_registry_from_records()





def ensure_patient_registry():

    registry = "Patients_Data.csv"

    if not os.path.exists(registry):

        df = pd.DataFrame(columns=[
        "UHID",
        "Name",
        "Diagnosis",
        "Status",
        "Admitted_On"
        ])
        df.to_csv(registry, index=False)

        print("✅ CLEAN Patient Registry Created")






@st.cache_data(ttl=10, show_spinner=False)
def load_patient_registry():
    """Cached read of Patients_Data.csv — refreshes every 10 seconds."""
    registry = "Patients_Data.csv"
    ensure_patient_registry()
    try:
        df = pd.read_csv(registry, on_bad_lines="skip")
        df["UHID"] = df["UHID"].astype(str).str.strip()
        df["Status"] = df["Status"].astype(str).str.strip()
        return df
    except Exception:
        return pd.DataFrame(columns=["UHID", "Name", "Diagnosis", "Status", "Admitted_On"])


def show_live_flash_notifications():

    if not os.path.exists(NOTIFICATION_FILE):
        return

    df = pd.read_csv(NOTIFICATION_FILE)

    if df.empty:
        return

    # Initialize last seen
    if "last_notification_count" not in st.session_state:
        st.session_state.last_notification_count = len(df)
        return

    current_count = len(df)
    previous_count = st.session_state.last_notification_count

    # If new notification added
    if current_count > previous_count:

        new_rows = df.iloc[previous_count:]

        for _, row in new_rows.iterrows():
            message = f"{row['Message']} | User: {row['User']} | Patient: {row['Patient']}"
            st.toast(message)

        st.session_state.last_notification_count = current_count

# ================= OT REGISTER SYSTEM =================

OT_REGISTER_FILE = "OT_Register.csv"
DAYCARE_REGISTER_FILE = "DayCare_Register.csv"

def rebuild_daycare_register():

    records_folder = "DayCare_Records"

    if not os.path.exists(records_folder):
        return

    rows = []

    for file in os.listdir(records_folder):

        file_path = os.path.join(records_folder, file)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            date = content.split("Date:")[1].split("\n")[0].strip()
            name = content.split("Patient Name:")[1].split("\n")[0].strip()
            diagnosis = content.split("Diagnosis:")[1].split("\n")[0].strip()
            procedure = content.split("Procedure:")[1].split("\n")[0].strip()
            surgeon = content.split("Surgeon:")[1].split("\n")[0].strip()

            rows.append({
                "Date": date,
                "Patient Name": name,
                "Diagnosis": diagnosis,
                "Procedure": procedure,
                "Surgeon": surgeon
            })

        except:
            pass

    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(DAYCARE_REGISTER_FILE, index=False)


@st.cache_resource(show_spinner=False)
def _rebuild_once():
    """Runs exactly once per server start — never on reruns."""
    rebuild_registry_from_records()
    rebuild_daycare_register()

_rebuild_once()


def save_ot_register_entry(date, patient_name, uhid, diagnosis, surgery, implant, nail_size, plate_type, holes, surgeon):

    entry = {
        "Date": str(date),
        "Patient Name": patient_name,
        "UHID": uhid,
        "Diagnosis": diagnosis,
        "Surgery": surgery,
        "Implant": implant,
        "Nail Size": nail_size,
        "Plate Type": plate_type,
        "Holes": holes,
        "Surgeon": surgeon
    }

    df_entry = pd.DataFrame([entry])

    if os.path.exists(OT_REGISTER_FILE):
        df_entry.to_csv(OT_REGISTER_FILE, mode='a', header=False, index=False)
    else:
        df_entry.to_csv(OT_REGISTER_FILE, index=False)
    
# =========================================
# DOCTOR MASTER DATABASE
# =========================================

DOCTOR_DATABASE = {
    "DR SIDDHARTH RASTOGI": {
        "degree": "MBBS, D.Ortho",
        "reg_no": "UPMCI-59557"
    },
    "DR RAJESH RASTOGI": {
        "degree": "MBBS, MS (Orthopaedics)",
        "reg_no": "UPMCI-67890"
    }
}


# =========================================================
# USER DATABASE
# =========================================================

USER_DB = "users.csv"

@st.cache_data(ttl=30, show_spinner=False)
def load_users():
    import pandas as pd
    data = load_users_sb()
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame(columns=["username", "password", "role", "status"])

def save_user(username, password, role):
    save_user_sb(username, password, role)

MASTER_ADMIN_SECRET = "Attitude@83"

# =========================================================
# PATIENT FUNCTIONS
# =========================================================

@st.cache_data(ttl=60, show_spinner=False)
def load_patient_name(uhid):
    return load_patient_name_sb(uhid)
@st.cache_data(ttl=300, show_spinner=False)
def load_admit_date(uhid):

    file_path = f"Records/{uhid}/Patient_Info.txt"

    if os.path.exists(file_path):

        with open(file_path, "r", encoding="utf-8") as f:

            for line in f.readlines():

                if "Admitted On:" in line:
                    return line.replace("Admitted On:", "").strip().split()[0]

    return "Unknown"


@st.cache_data(ttl=30, show_spinner=False)
def patient_exists(uhid):
    return patient_exists_sb(uhid)




def register_patient(uhid, patient_name, diagnosis, admitted_on):
    
    ensure_patient_registry()

    registry = "Patients_Data.csv"

    df = pd.read_csv(registry, on_bad_lines='skip')

    new_entry = pd.DataFrame([{
        "UHID": str(uhid).strip(),
        "Name": patient_name.strip().upper(),
        "Diagnosis": diagnosis.strip(),
        "Status": "Admitted",
        "Admitted_On": admitted_on
    }])

    df = pd.concat([df, new_entry], ignore_index=True)

    df.to_csv(registry, index=False)
    

    print("✅ PATIENT SAVED:", uhid)

    
    register_patient_sb(uhid, patient_name, diagnosis, admitted_on)


def get_patient_list():

    if not os.path.exists("Records"):
        return []

    patients = []

    st.subheader("📋 Admitted Patients")

    ensure_patient_registry()
    # ALSO LOAD FROM HIS SQL
    try:

        conn = sqlite3.connect("hospital.db")

        df_sql = pd.read_sql_query("""
            SELECT name, uhid
            FROM opd_live
            ORDER BY date DESC
            LIMIT 50
        """, conn)

        conn.close()

        for _, r in df_sql.iterrows():

            patients.append({
                "UHID": str(r["uhid"]),
                "Patient Name": r["name"]
            })

    except:
        pass



    df = pd.read_csv("Patients_Data.csv", on_bad_lines='skip')

    df["UHID"] = df["UHID"].astype(str).str.strip()
    df["Status"] = df["Status"].astype(str).str.strip()

    admitted_patients = df[df["Status"] == "Admitted"]

    if admitted_patients.empty:

        st.info("No Admitted Patients ✅")

    else:

        for _, row in admitted_patients.iterrows():

            uhid = row["UHID"]
            name = row["Name"]

            if st.button(f"🟢 {name}", key=f"patient_{uhid}"):

                st.session_state.selected_patient = uhid
                st.session_state.page = "patient_dashboard"
                st.rerun()

        info_path = f"Records/{uhid}/Patient_Info.txt"

        if os.path.exists(info_path):

            name = load_patient_name(uhid)

            patients.append({
                "UHID": uhid,
                "Patient Name": name
            })

    return pd.DataFrame(patients)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"   # ✅ BETTER than localhost

def generate_ai_ot_note(patient_name, diagnosis, procedure, findings):

    prompt = f"""
Write a detailed orthopedic operative note.

Patient Name: {patient_name}

Diagnosis:
{diagnosis}

Procedure:
{procedure}

Operative Findings:
{findings}
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "mistral",   # ✅ MOST RELIABLE
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        st.write("STATUS CODE:", response.status_code)   # DEBUG
        st.write("RAW TEXT:", response.text)             # DEBUG

        data = response.json()

        ai_text = data.get("response", "")

        if ai_text.strip() == "":
            return "⚠ AI Returned Empty Response"

        return ai_text

    except Exception as e:

        st.write("🚨 REAL ERROR:", str(e))   # 🔥 THIS IS KEY

        return "AI FAILED"

def check_daily_compliance():

    today = datetime.now().strftime("%d-%m-%Y")

    non_compliant_patients = []
    compliant_patients = []

    if not os.path.exists("Records"):
        return compliant_patients, non_compliant_patients

    for uhid in os.listdir("Records"):

        vital_file = f"Records/{uhid}/Vitals_Log.csv"
        med_file = f"Records/{uhid}/Medication_Log.csv"

        vitals_done = False
        meds_done = False

        if os.path.exists(vital_file):
            df_vitals = pd.read_csv(vital_file, on_bad_lines='skip') 
            if today in df_vitals["Date"].values:
                vitals_done = True

        if os.path.exists(med_file):
            df_med = pd.read_csv(med_file)
            if today in df_med["Date"].values:
                meds_done = True

        if vitals_done and meds_done:
            compliant_patients.append(uhid)
        else:
            non_compliant_patients.append(uhid)

    return compliant_patients, non_compliant_patients


def build_ot_prompt(patient_name, diagnosis, surgery_type, findings):

    
    templates = {

        "Malleolar Screw Fixation": f"""
Write a detailed orthopaedic operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Open reduction and internal fixation of malleolar fracture using cancellous screws under spinal anaesthesia.

Operative Findings:
{findings}

Include:
• Patient positioning
• Surgical approach
• Fracture reduction
• Screw fixation
• Stability check
• Closure
• Postoperative plan
""",

        "Proximal Tibia Locking Plate": f"""
Write a detailed orthopaedic operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Open reduction and internal fixation of proximal tibial plateau fracture using locking plate under spinal anaesthesia.

Operative Findings:
{findings}

Include reduction technique, plate fixation, alignment restoration, closure, and postop protocol.
""",

        "Forearm Square Nailing": f"""
Write a detailed orthopaedic operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Closed reduction and internal fixation of forearm fracture using square nail.

Operative Findings:
{findings}
""",

        "Both Bone Plating": f"""
Write a professional operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Open reduction and internal fixation of both bone forearm fracture using plating.

Operative Findings:
{findings}

Include exposure, reduction, plate fixation, screw placement, and closure.
""",

        "External Fixator": f"""
Write a detailed operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Application of external fixator under appropriate anaesthesia.

Operative Findings:
{findings}

Include pin placement, frame assembly, alignment, stability, closure.
""",

        "JESS Application": f"""
Write a detailed orthopaedic operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Application of JESS external fixator.

Operative Findings:
{findings}
""",

        "Hemiarthroplasty (AMP Prosthesis)": f"""
Write a professional hemiarthroplasty operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Hemiarthroplasty using Austin Moore Prosthesis.

Operative Findings:
{findings}

Include approach, head excision, canal preparation, prosthesis insertion, stability, closure.
""",

        "Skin Grafting": f"""
Write a detailed operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Split thickness skin grafting.

Operative Findings:
{findings}
""",

        "Debridement": f"""
Write a detailed operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Surgical wound debridement.

Operative Findings:
{findings}
""",

        "K-Wire Fixation": f"""
Write a detailed orthopaedic operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Fracture fixation using K-wires.

Operative Findings:
{findings}
""",

        "CC Screw Fixation": f"""
Write a detailed orthopaedic operative note.

Patient Name: {patient_name}
Diagnosis: {diagnosis}

Procedure:
Fixation using cancellous screws.

Operative Findings:
{findings}
"""
    }

    return templates.get(surgery_type, "Write operative note")



def load_discharge_status(uhid):
    file_path = f"Records/{uhid}/Discharge_Info.txt"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read()
    return None

@st.cache_data(ttl=10, show_spinner=False)
def load_patient_status(uhid):
    return load_patient_status_sb(uhid)


def discharge_patient(uhid):

    registry = "Patients_Data.csv"

    ensure_patient_registry()

    df = pd.read_csv(registry, on_bad_lines='skip')

    # ✅ CLEAN EVERYTHING
    df["UHID"] = df["UHID"].astype(str).str.strip()
    df["Status"] = df["Status"].astype(str).str.strip()

    uhid = str(uhid).strip()

    # ✅ DEBUG (optional but powerful)

    if uhid not in df["UHID"].values:
        st.error("🚨 UHID NOT FOUND IN REGISTRY")
        return "ERROR"

    df.loc[df["UHID"] == uhid, "Status"] = "Discharged"

    df.to_csv(registry, index=False)


    return datetime.now().strftime("%d-%m-%Y")


def reverse_discharge_patient(uhid):

    registry = "Patients_Data.csv"

    df = pd.read_csv(registry, on_bad_lines='skip')

    df["UHID"] = df["UHID"].astype(str).str.strip()

    uhid = str(uhid).strip()

    df.loc[df["UHID"] == uhid, "Status"] = "Admitted"

    df.to_csv(registry, index=False)

    return True

def readmit_patient(uhid):

    df = pd.read_csv("Patients_Data.csv", on_bad_lines='skip')

    df.loc[df["UHID"] == uhid, "Status"] = "Admitted"

    df.to_csv("Patients_Data.csv", index=False)

    return datetime.now().strftime("%d-%m-%Y")


def load_discharge_date(uhid):

    file_path = f"Records/{uhid}/Discharge_Info.txt"

    if os.path.exists(file_path):

        with open(file_path, "r", encoding="utf-8") as f:

            for line in f.readlines():

                if "Date:" in line:
                    return line.replace("Date:", "").strip()

    return "N/A"


def check_critical_vitals(pulse, bp, rr):

    try:

        if pulse and int(pulse) > 120:
            st.error("🚨 Tachycardia Alert")

        if bp and "/" in bp:

            systolic = int(bp.split("/")[0])

            if systolic > 180:
                st.error("🚨 Hypertensive Crisis")

        if rr and int(rr) > 30:
            st.error("🚨 Respiratory Distress")

    except:
        pass





def invalidate_cache():
    """Call this after any write operation to force cache refresh."""
    load_patient_registry.clear()
    load_users.clear()
    load_latest_diagnosis.clear()
    load_patient_status.clear()


def exit_system():
    st.session_state.page = "login"
    st.session_state.selected_patient = ""
    st.session_state.user = ""


AUDIT_FILE = "Audit_Trail.csv"

NOTIFICATION_FILE = "notifications.csv"

SUMMARY_APPROVAL_FILE = "summary_approvals.csv"


def add_notification(message, user="", patient=""):
    add_notification_sb(message, user=user, patient=patient)

def log_audit(action, user="", patient="", details=""):
    log_audit_sb(action, user=user, patient=patient, details=details)

def request_summary_approval(uhid, requested_by):
    request_summary_approval_sb(uhid, requested_by)


def check_summary_status(uhid):
    return check_summary_status_sb(uhid)


def approve_summary(uhid):
    approve_summary_sb(uhid)


# =========================================================
# PDF ENGINE
# =========================================================
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfgen import canvas   # ✅ ADD THIS

styles = getSampleStyleSheet()
style = styles['BodyText']

HOSPITAL_NAME = "MAHAVEER HOSPITAL & DENTAL CARE PRIVATE LIMITED"

def ot_done(uhid):
    return ot_done_sb(uhid)

def add_watermark(c, doc):
    c.saveState()
    c.setFont("Helvetica-Bold", 40)
    c.setFillColor(colors.lightgrey)
    c.translate(300, 400)
    c.rotate(45)
    c.drawCentredString(0, 0, HOSPITAL_NAME)
    c.restoreState()


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch



def generate_pdf(file_path, lines):

    c = canvas.Canvas(file_path, pagesize=A4)

    width, height = A4

    x_start = 1.0 * inch
    y_start = height - (2.6 * inch)

    line_height = 18
    y = y_start

    c.setFont("Helvetica", 12)

    for line in lines:

        if y <= 2.1 * inch:
            break

        c.drawString(x_start, y, line)
        y -= line_height

    from datetime import datetime
    today = datetime.now().strftime("%d-%m-%Y")

    c.drawRightString(width - 1 * inch, height - 2.3 * inch, f"Date: {today}")

    c.drawRightString(width - 1 * inch, 2.3 * inch, "Doctor Signature")

    c.save()


def show_pdf_preview(pdf_path):
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")

        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}"
        width="100%" height="600px"></iframe>
        """

        st.markdown(pdf_display, unsafe_allow_html=True)

@st.cache_data(ttl=60, show_spinner=False)
def load_latest_diagnosis(uhid):
    return load_latest_diagnosis_sb(uhid)


def predict_vitals(diagnosis):

    diagnosis = diagnosis.lower()

    pulse_range = (72, 88)
    rr_range = (14, 20)
    systolic_range = (110, 130)
    diastolic_range = (70, 90)

    if "fracture" in diagnosis:
        pulse_range = (78, 96)
        rr_range = (16, 22)

    if "trauma" in diagnosis:
        pulse_range = (88, 110)
        rr_range = (18, 26)

    if "post" in diagnosis:
        pulse_range = (80, 100)
        rr_range = (16, 24)

    if "fever" in diagnosis or "infection" in diagnosis:
        pulse_range = (96, 120)
        rr_range = (20, 30)

    pulse = random.randint(*pulse_range)
    rr = random.randint(*rr_range)

    systolic = random.randint(*systolic_range)
    diastolic = random.randint(*diastolic_range)

    bp = f"{systolic}/{diastolic}"

    return pulse, bp, rr


def auto_fill_vitals_if_missing(uhid, diagnosis):

    vital_file = f"Records/{uhid}/Vitals_Log.csv"

    today = datetime.now()
    today_str = today.strftime("%d-%m-%Y")

    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%d-%m-%Y")

    os.makedirs(f"Records/{uhid}", exist_ok=True)

    # ✅ LOAD EXISTING DATA
    if os.path.exists(vital_file):

        df_vitals = pd.read_csv(vital_file)

        dates = df_vitals["Date"].astype(str).values

        # ✅ IF TODAY EXISTS → EXIT
        if today_str in dates:
            return

        # ✅ IF YESTERDAY EXISTS → NORMAL CASE → EXIT
        if yesterday_str in dates:
            return

    # ✅ SMART AUTO ENTRY (MISSED CASE)
    pulse, bp, rr = predict_vitals(diagnosis)

    entry = {
        "Date": today_str,
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Pulse": pulse,
        "BP": bp,
        "RR": rr,
        "Source": "AUTO (Missed Previous Day)"
    }

    file_exists = os.path.exists(vital_file)

    with open(vital_file, "a", newline="") as f:

        writer = csv.DictWriter(f, fieldnames=entry.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(entry)


def generate_ai_ot_note_v2(patient_name, diagnosis, surgery_type, findings):


    prompt = build_ot_prompt(
        patient_name,
        diagnosis,
        surgery_type,
        findings
    )


    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False
            }
        )


        data = response.json()

        return data["response"]

    except Exception as e:
        return "AI FAILED"

# =========================================================
# LOGIN PAGE
# =========================================================
if st.session_state.page == "login":

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #f0f4f8; }
    .hosp-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .hosp-header h1 {
        color: #1565C0;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
    }
    .hosp-header p {
        color: #666;
        font-size: 0.95rem;
        margin: 4px 0 0 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 2px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        justify-content: center;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.75rem;
        background: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #1565C0 !important;
        border-bottom: 3px solid #1565C0 !important;
    }
    </style>
    <div class="hosp-header">
        <h1>🏥 Mahaveer Hospital</h1>
        <p>Clinical Management System</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Ensure default admin exists ──────────────────────────────────────────
    @st.cache_resource(show_spinner=False)
    def _ensure_default_admin():
        try:
            r = supabase.table("users").select("username") \
                .eq("username", "admin").execute()
            if not r.data:
                supabase.table("users").insert({
                    "username": "admin",
                    "password": "Admin@Hospital1",
                    "role":     "Admin",
                    "status":   "Approved"
                }).execute()
        except Exception:
            pass
    _ensure_default_admin()

    _, col, _ = st.columns([1, 2, 1])
    with col:
        tab_login, tab_signup = st.tabs(["🔐  Login", "📝  Sign Up"])

        # ── LOGIN TAB ────────────────────────────────────────────────────────
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            l_user = st.text_input("Username", placeholder="Enter username", key="l_user")
            l_pass = st.text_input("Password", type="password", placeholder="Enter password", key="l_pass")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🔐  Login", use_container_width=True, key="login_btn"):
                if not l_user.strip() or not l_pass.strip():
                    st.warning("Please enter both username and password.")
                else:
                    try:
                        result = supabase.table("users") \
                            .select("*") \
                            .eq("username", l_user.strip()) \
                            .eq("password", l_pass.strip()) \
                            .execute()
                        matches = result.data
                        if matches:
                            user = matches[0]
                            if user.get("status", "Approved") != "Approved":
                                st.error("⏳ Account pending Admin approval.")
                            else:
                                role = user["role"]
                                st.session_state.user      = l_user.strip()
                                st.session_state.role      = role
                                st.session_state.logged_in = True
                                st.session_state.page = {
                                    "Doctor":     "doctor_dashboard",
                                    "Nurse":      "nurse_dashboard",
                                    "Technician": "tech_dashboard",
                                    "Reception":  "reception_dashboard",
                                    "Admin":      "admin_dashboard",
                                }.get(role, "doctor_dashboard")
                                st.rerun()
                        else:
                            st.error("❌ Invalid username or password.")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

            st.markdown("---")
            st.caption("🔑 Default Admin — username: `admin`  password: `Admin@Hospital1`")

        # ── SIGN UP TAB ──────────────────────────────────────────────────────
        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("New accounts require Admin approval before you can log in.")

            s_name = st.text_input("Full Name", placeholder="Dr. / Staff name", key="s_name")
            s_user = st.text_input("Username", placeholder="Choose a username", key="s_user")
            s_pass = st.text_input("Password", type="password",
                                   placeholder="Min 6 characters", key="s_pass")
            s_pass2 = st.text_input("Confirm Password", type="password",
                                    placeholder="Repeat password", key="s_pass2")
            s_role = st.selectbox("Role",
                ["Doctor", "Nurse", "Technician", "Reception"],
                key="s_role")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("📝  Request Account", use_container_width=True, key="signup_btn"):
                if not s_user.strip() or not s_pass.strip() or not s_name.strip():
                    st.warning("Please fill in all fields.")
                elif len(s_pass) < 6:
                    st.warning("Password must be at least 6 characters.")
                elif s_pass != s_pass2:
                    st.error("Passwords do not match.")
                else:
                    try:
                        # Check username not taken
                        existing = supabase.table("users") \
                            .select("username") \
                            .eq("username", s_user.strip()) \
                            .execute()
                        if existing.data:
                            st.error("❌ Username already exists. Choose another.")
                        else:
                            supabase.table("users").insert({
                                "username": s_user.strip(),
                                "password": s_pass.strip(),
                                "role":     s_role,
                                "status":   "Pending",
                                "name":     s_name.strip(),
                            }).execute()
                            st.success(
                                f"✅ Account requested for **{s_name}** ({s_role}). "
                                "Please wait for Admin approval."
                            )
                    except Exception as e:
                        st.error(f"Error: {e}")

# ── Background HIS sync ───────────────────────────────────────────────────────
if st.session_state.get("logged_in") and "sync_started" not in st.session_state:
    try:
        from sync_his_to_supabase import sync
        def _bg_sync():
            while True:
                try: sync()
                except Exception: pass
                time.sleep(10)
        threading.Thread(target=_bg_sync, daemon=True).start()
        st.session_state.sync_started = True
    except Exception:
        pass  # sync module may not be available on cloud


if st.session_state.page == "doctor_dashboard":
     
    st.title("👨‍⚕️ Doctor Dashboard")
    st.write("Logged User:", st.session_state.user) 

    st_autorefresh(interval=15000, key="live_refresh")  # 15s refresh

    show_live_flash_notifications()

    if st.button("🩺 My OPD Queue"):
        st.session_state.page = "doctor_opd"
        st.rerun()

    df_patients = get_patient_list()


# ensure df_patients is DataFrame
    if isinstance(df_patients, list):
        df_patients = pd.DataFrame(df_patients)

    if df_patients is None or df_patients.empty:
        st.info("No Patients Found")

        

    else:

        for _, row in df_patients.iterrows():

            uhid = row["UHID"]
            patient_name = row["Patient Name"]

            vital_file = f"Records/{uhid}/Vitals_Log.csv"

            vitals_done = False

            if os.path.exists(vital_file):

                df_vitals = pd.read_csv(vital_file, on_bad_lines='skip')

                today = datetime.now().strftime("%d-%m-%Y")

                if today in df_vitals["Date"].values:
                    vitals_done = True

            if vitals_done:

                if st.button(f"🟢 {patient_name}", key=f"doc_{uhid}"):

                    st.session_state.selected_patient = uhid
                    st.session_state.page = "patient_dashboard"
                    st.rerun()

            else:

                if st.button(f"🔴 {patient_name} (Vitals Pending)", key=f"doc_{uhid}"):

                    st.session_state.selected_patient = uhid
                    st.session_state.page = "patient_dashboard"
                    st.rerun()

    st.markdown("---")

    if st.button("🔍 Search Patient"):

        st.session_state.page = "search"
        st.rerun()
    
    if st.button("🏥 Day Care Surgery", key="doctor_daycare_btn"):

        st.session_state.page = "daycare"
        st.rerun()
    
    

# 🔥 ADD THIS BELOW

    if st.button("📘 Day Care Register", key="doctor_daycare_register"):
        st.session_state.page = "daycare_register"
        st.rerun()
    
    

    uhid_check = st.text_input("Enter UHID")

    if st.button("Open Patient Record"):

        if os.path.exists(f"Records/{uhid_check}"):

            st.session_state.selected_patient = uhid_check
            st.session_state.page = "patient_dashboard"
            st.rerun()

        else:

            st.error("Patient record not found")

    st.markdown("---")

    if st.button("🗑 Delete"):
        st.session_state.delete_attempts = 0   # ✅ Reset attempts
        st.session_state.page = "delete_auth"
        st.rerun()
    

    st.markdown("---")
    st.subheader("📘 Pending Summary Approvals")

    if os.path.exists(SUMMARY_APPROVAL_FILE):

        df = pd.read_csv(SUMMARY_APPROVAL_FILE)

        pending = df[df["Status"] == "Pending"]

        if pending.empty:
            st.info("No Pending Requests")

        else:
            for _, row in pending.iterrows():

                uhid = row["UHID"]

                col1, col2 = st.columns([3,1])

                with col1:
                    st.write(f"UHID: {uhid}")

                with col2:
                    if st.button("Approve", key=f"approve_{uhid}"):

                        approve_summary(uhid)

                        st.success("Approved")
                        st.rerun()

    
    if st.button("🚪 Exit"):

        exit_system()
        st.rerun()

    st.markdown("---")
    st.subheader("🛡 User Approval Panel")

    df_users = load_users()

    pending_users = df_users[df_users["Status"] == "Pending"]

    if pending_users.empty:
        st.info("No Pending Users")
    else:
        for index, row in pending_users.iterrows():

            col1, col2 = st.columns([3,1])

            with col1:
                st.write(f"{row['Username']} ({row['Role']})")

            with col2:
                if st.button("Approve", key=f"approve_{index}"):

                    df_users.loc[index, "Status"] = "Approved"
                    df_users.to_csv(USER_DB, index=False)

                    st.success(f"{row['Username']} Approved")
                    add_notification(
                        message="User Approved",
                        user=row['Username']
                    )

                    st.rerun()

# =========================================================
# NURSE DASHBOARD
# =========================================================

# =========================================================
# FULL NURSING STATION
# =========================================================

elif st.session_state.page == "nurse_dashboard":

    st.title("👩‍⚕️ NURSING STATION CONTROL PANEL")

    st.markdown(f"Logged in as: **{st.session_state.user}**")

    st.markdown("---")

    # =========================================
    # 🏥 LIVE PATIENT CENSUS
    # =========================================

    st.subheader("🏥 Live Admitted Census")

    if os.path.exists("Patients_Data.csv"):

        df = pd.read_csv("Patients_Data.csv", on_bad_lines="skip")
        admitted = df[df["Status"] == "Admitted"]

        total = len(admitted)

        st.metric("Currently Admitted Patients", total)

    st.markdown("---")

    # =========================================
    # 🔴 CRITICAL VITAL ALERTS
    # =========================================

    st.subheader("🚨 Critical Alert Monitor")

    critical_list = []

    if os.path.exists("Records"):

        for uhid in os.listdir("Records"):

            vital_file = f"Records/{uhid}/Vitals_Log.csv"

            if os.path.exists(vital_file):

                df_v = pd.read_csv(vital_file, on_bad_lines="skip")

                if not df_v.empty:

                    last = df_v.iloc[-1]

                    try:
                        pulse = int(last["Pulse"])
                        bp = last["BP"]
                        rr = int(last["RR"])

                        if pulse > 120 or rr > 30:
                            critical_list.append(uhid)

                        if "/" in str(bp):
                            sys = int(bp.split("/")[0])
                            if sys > 180:
                                critical_list.append(uhid)

                    except:
                        pass

    if critical_list:
        st.error(f"⚠ Critical Patients: {len(critical_list)}")
        st.write(critical_list)
    else:
        st.success("No Critical Alerts")

    st.markdown("---")

    # =========================================
    # 📋 DAILY COMPLIANCE
    # =========================================

    st.subheader("📋 Daily Compliance")

    compliant, non_compliant = check_daily_compliance()

    col1, col2 = st.columns(2)

    col1.metric("Compliant", len(compliant))
    col2.metric("Non-Compliant", len(non_compliant))

    if non_compliant:
        st.warning("Patients Missing Entries Today")
        st.write(non_compliant)

    st.markdown("---")

    # =========================================
    # 💊 MEDICATION MONITOR
    # =========================================

    st.subheader("💊 Medication Monitor")

    today = datetime.now().strftime("%d-%m-%Y")

    med_pending = []

    for uhid in os.listdir("Records"):

        med_file = f"Records/{uhid}/Medication_Log.csv"

        if os.path.exists(med_file):

            df_med = pd.read_csv(med_file, on_bad_lines="skip")

            if today not in df_med["Date"].values:
                med_pending.append(uhid)

    if med_pending:
        st.warning(f"{len(med_pending)} Patients Pending Medication Entry")
    else:
        st.success("All Medication Updated Today")

    st.markdown("---")

    # =========================================
    # 📝 NURSING NOTES
    # =========================================

    st.subheader("📝 Add Nursing Notes")

    df_patients = get_patient_list()

    if not df_patients.empty:

        selected = st.selectbox(
            "Select Patient",
            df_patients["UHID"]
        )

        note = st.text_area("Nursing Note")

        if st.button("Save Nursing Note"):

            os.makedirs(f"Records/{selected}", exist_ok=True)

            note_file = f"Records/{selected}/Nursing_Notes.txt"

            with open(note_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now()}] {note}\n")

            st.success("Nursing Note Saved")

    st.markdown("---")

    # =========================================
    # 🔄 SHIFT HANDOVER REPORT
    # =========================================

    st.subheader("🔄 Shift Handover Report")

    if st.button("Generate Shift Report"):

        report = f"NURSING SHIFT REPORT - {datetime.now()}\n\n"

        report += f"Total Admitted: {total}\n"
        report += f"Critical Cases: {len(critical_list)}\n"
        report += f"Non-Compliant: {len(non_compliant)}\n"

        st.text(report)

    st.markdown("---")

    if st.button("🚪 Exit"):
        exit_system()
        st.rerun()


elif st.session_state.page == "pharmacy_dashboard":
    pharmacy_dashboard()

    if st.button("↩ Back"):
        st.session_state.page = "admin_dashboard"
        st.rerun()    

# =========================================================
# SEARCH PAGE
# =========================================================

elif st.session_state.page == "search":

    st.title("🔍 Patient Search")
    patients = os.listdir("Records")

    selected = st.selectbox("Select Patient Record", patients)

    if st.button("Open Record"):

        st.session_state.selected_patient = selected
        st.session_state.page = "patient_dashboard"
        st.rerun()

    search = st.text_input(
        "Search Patient Name or UHID",
        placeholder="Type at least 2 characters..."
    )

    results = []

# Only search if user typed at least 2 characters
    if search and len(search.strip()) >= 2:

        search = search.strip()

    # ------------------------
    # SEARCH OPD (SQL)
    # ------------------------
        result = supabase.table("opd_live")\
            .select("name,uhid,date")\
            .ilike("name", f"%{search}%")\
            .limit(20)\
            .execute()

        for r in result.data:

            results.append({
                "name": r["name"],
                "uhid": str(r["uhid"]),
                "date": str(r["date"]),
                "type": "OPD"
            })

    # ------------------------
    # SEARCH IPD (CSV)
    # ------------------------
        if os.path.exists("Patients_Data.csv"):

            df = pd.read_csv("Patients_Data.csv", on_bad_lines="skip")

            df["UHID"] = df["UHID"].astype(str)
            df["Name"] = df["Name"].astype(str)

            ipd = df[
                df["UHID"].str.contains(search, case=False, na=False) |
                df["Name"].str.contains(search, case=False, na=False)
            ]

            for _, r in ipd.iterrows():

                results.append({
                    "name": r["Name"],
                    "uhid": r["UHID"],
                    "date": r.get("Admit Date",""),
                    "type": "IPD"
                })

# ------------------------
# DISPLAY RESULTS
# ------------------------
    if results:

        st.subheader("Matching Patients")

        for i, r in enumerate(results):

            col1, col2, col3, col4, col5 = st.columns([3,2,1,2,1])

            col1.write(f"👤 {r.get('name','')}")
            col2.write(f"UHID: {r.get('uhid','')}")
            col3.write(r.get("type",""))
            col4.write(r.get("date",""))

            if col5.button("Admit", key=f"open_{r.get('uhid','')}_{i}"):

                st.session_state.selected_patient = r.get("uhid","")
                st.session_state.page = "patient_dashboard"
                st.rerun()

    elif search:
        st.warning("No patient found")


# =========================================================
# NEW PATIENT PAGE
# =========================================================

elif st.session_state.page == "new_patient":

    st.title("➕ IPD Patient Admission")

    st.divider()

    # =========================
    # 🔍 SEARCH PATIENT
    # =========================

    st.subheader("🔍 Search Patient")

    search = st.text_input("Search by Patient Name or UHID")

    if search and len(search) >= 2:

        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, uhid
            FROM opd_live
            WHERE name LIKE ? OR uhid LIKE ?
            ORDER BY date DESC
            LIMIT 10
        """, (f"%{search}%", f"%{search}%"))

        results = cursor.fetchall()

        conn.close()

        if results:

            st.write("Matching Patients")

            for i, r in enumerate(results):

                col1, col2, col3 = st.columns([3,2,1])

                col1.write(r[0])
                col2.write(f"UHID: {r[1]}")

                if col3.button("Select", key=f"select_{i}"):

                    st.session_state.selected_patient = str(r[1])
                    st.session_state.selected_name = r[0]

                    st.rerun()

        else:
            st.warning("No patient found")

    st.divider()

    # =========================
    # 🏥 ADMISSION FORM
    # =========================

    st.subheader("🏥 Admit Patient")

    uhid = st.session_state.get("selected_patient","")
    patient_name = st.session_state.get("selected_name","")

    uhid = st.text_input("UHID", value=uhid)
    patient_name = st.text_input("Patient Name", value=patient_name).upper()

    age = st.text_input("Age")

    gender = st.selectbox(
        "Gender",
        ["Male","Female","Other"]
    )

    diagnosis = st.text_input("Diagnosis")

    admit_date = st.date_input(
        "Admission Date",
        datetime.now()
    )

    admit_time = st.time_input(
        "Admission Time",
        datetime.now().time()
    )

    if st.button("🏥 Admit Patient"):

        if uhid.strip() == "" or patient_name.strip() == "":
            st.error("UHID and Patient Name required")
            st.stop()

        registry = "Patients_Data.csv"

        if os.path.exists(registry):

            df = pd.read_csv(registry)

            df["UHID"] = df["UHID"].astype(str)

            existing = df[
                (df["UHID"] == uhid) &
                (df["Status"] == "Admitted")
            ]

            if not existing.empty:

                st.error("⚠ Patient already admitted")
                st.stop()

        # =========================
        # CREATE PATIENT FOLDER
        # =========================

        folder = f"Records/{uhid}"
        os.makedirs(folder, exist_ok=True)

        admitted_on = f"{admit_date.strftime('%d-%m-%Y')} {admit_time.strftime('%H:%M:%S')}"

        with open(f"{folder}/Patient_Info.txt","w") as f:

            f.write(f"Patient Name: {patient_name}\n")
            f.write(f"Diagnosis: {diagnosis}\n")
            f.write(f"Age: {age}\n")
            f.write(f"Gender: {gender}\n")
            f.write(f"Admitted On: {admitted_on}\n")

        # =========================
        # SAVE TO REGISTRY
        # =========================

        new_entry = pd.DataFrame([{
            "UHID": uhid,
            "Name": patient_name,
            "Diagnosis": diagnosis,
            "Status": "Admitted",
            "Admitted_On": admitted_on
        }])

        if os.path.exists(registry):

            new_entry.to_csv(registry, mode="a", header=False, index=False)

        else:

            new_entry.to_csv(registry, index=False)

        st.success("✅ Patient Admitted Successfully")

        st.session_state.selected_patient = uhid
        st.session_state.page = "patient_dashboard"

        st.rerun()


# =========================================================
# DELETE AUTH PAGE (PIN ENTRY)
# =========================================================

elif st.session_state.page == "delete_auth":

    st.title("🔐 Security Verification")

    pin = st.text_input("Enter Security PIN", type="password")

    CONFIRM_PIN = "1234"   # 🔥 CHANGE PIN

    if "delete_attempts" not in st.session_state:
        st.session_state.delete_attempts = 0

    if st.button("Verify PIN"):

        if pin == CONFIRM_PIN:

            st.session_state.page = "delete_manage"
            st.rerun()

        else:

            st.session_state.delete_attempts += 1

            remaining = 3 - st.session_state.delete_attempts

            if remaining > 0:
                st.error(f"❌ Incorrect PIN | Attempts Left: {remaining}")
            else:
                st.error("🚨 Too Many Incorrect Attempts")
                st.session_state.page = "doctor_dashboard"
                st.rerun()

    if st.button("↩ Cancel"):
        st.session_state.page = "doctor_dashboard"
        st.rerun()

# =========================================================
# RECEPTION DASHBOARD
elif st.session_state.page == "reception_dashboard":

    st.title("🧾 Reception Desk")
    st.markdown(f"Logged in as: **{st.session_state.user}**")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    # 🏥 OPD
    with col1:
        if st.button("🏥 OPD", use_container_width=True):
            st.session_state.page = "live_opd"
            st.rerun()

    # 🛏 IPD
    with col2:
        if st.button("🛏 IPD", use_container_width=True):
            st.session_state.page = "ipd_dashboard"   # or your IPD page
            st.rerun()

    # 📄 CERTIFICATE
    with col3:
        if st.button("📄 Certificate", use_container_width=True):
            st.session_state.page = "medical_fitness_certificate"
            st.rerun()


    # 🌐 ONLINE APPOINTMENTS
    with col4:
        if st.button("🌐 Online Appointments", use_container_width=True):
            st.session_state.page = "online_appointments"
            st.rerun()

    st.markdown("---")
    
    if st.button("↩ Back"):
        st.session_state.page = "reception_dashboard"
        st.rerun()
    

    if st.button("🚪 Exit"):
        exit_system()
        st.rerun()

# =========================================================
# IPD DASHBOARD
# =========================================================

elif st.session_state.page == "ipd_dashboard":

    st.title("🛏 IPD Control Panel")
    st.markdown(f"Logged in as: **{st.session_state.user}**")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    # ➕ NEW PATIENT ADMISSION
    with col1:
        if st.button("➕ New Admission", use_container_width=True):
            st.session_state.page = "new_patient"
            st.rerun()

    # 🔍 SEARCH EXISTING
    with col2:
        if st.button("🔍 Search Patient", use_container_width=True):
            st.session_state.page = "search"
            st.rerun()

    # 📋 ADMITTED LIST
    with col3:
        if st.button("📋 Admitted Patients", use_container_width=True):
            st.session_state.page = "patient_dashboard"
            st.rerun()

    st.markdown("---")

    if st.button("↩ Back"):
        st.session_state.page = "reception_dashboard"
        st.rerun()

# =========================================================
# =========================================================
# RECEPTION DASHBOARD
# =========================================================
# =========================================================
# LIVE OPD PANEL
# =========================================================
# ONLINE APPOINTMENTS PAGE
# =========================================================

elif st.session_state.page == "online_appointments":

    st.title("🌐 Online Appointments")

    conn = sqlite3.connect("hospital.db")

    df = pd.read_sql_query(
    """
    SELECT name, mobile, date, time, department
    FROM opd_live
    WHERE source='ONLINE'
    ORDER BY date DESC, time ASC
    """,
    conn
    )

    if df.empty:
        st.info("No Online Appointments")

    else:
        st.dataframe(df, use_container_width=True)

    conn.close()

    if st.button("↩ Back", key="back_online"):
        st.session_state.page = "reception_dashboard"
        st.rerun()



# =========================================================
elif st.session_state.page == "live_opd":

    if st.button("↩ Back"):
        st.session_state.page = "reception_dashboard"
        st.rerun()

    from opd import opd_reception_panel
    opd_reception_panel()


# =========================================================
# DOCTOR OPD PANEL
# =========================================================

elif st.session_state.page == "doctor_opd":

    # 🔙 Back Button at Top
    if st.button("↩ Back to Doctor Dashboard", key="back_doc_dashboard_doctor"):
        st.session_state.page = "doctor_dashboard"
        st.rerun()

    from opd import opd_doctor_panel
    opd_doctor_panel(st.session_state.user)

# =========================================================
# PATIENT DASHBOARD
# =========================================================
elif st.session_state.page == "patient_dashboard":
    
    st.write("🧭 ACTIVE PAGE:", st.session_state.page)
    st.write("👤 SELECTED PATIENT:", st.session_state.selected_patient)
    
    uhid = st.session_state.get("selected_patient")

    diagnosis = load_latest_diagnosis(uhid) if uhid else "General Case"

    if uhid:
        auto_fill_vitals_if_missing(uhid, diagnosis)

    vital_file = f"Records/{uhid}/Vitals_Log.csv"

    st.title("🏥 Patient Dashboard")

    patient_name = load_patient_name(uhid) if uhid else "Unknown Patient"

    patient_status = load_patient_status(uhid)

    

    # =========================================================
    # 👤 PATIENT INFO + DIAGNOSIS EDITOR
    # =========================================================

    st.markdown("### 👤 Patient Information")

    st.info(f"""
    👤 **{patient_name}**

    🩺 **Diagnosis:**
    {diagnosis}
    """)

    st.markdown("---")
    st.subheader("✏️ Edit Diagnosis")

    edited_diagnosis = st.text_area(
        "Update / Add Diagnosis Details",
        value=diagnosis,
        height=120
    )

    if st.button("💾 Save Diagnosis", key="save_diag"):

        os.makedirs(f"Records/{uhid}", exist_ok=True)

        with open(f"Records/{uhid}/Diagnosis.txt", "w", encoding="utf-8") as f:
            f.write(edited_diagnosis.strip())

        df = pd.read_csv("Patients_Data.csv", on_bad_lines='skip')

        df["UHID"] = df["UHID"].astype(str)

        df.loc[df["UHID"] == str(uhid), "Diagnosis"] = edited_diagnosis.strip()

        df.to_csv("Patients_Data.csv", index=False)

        st.success("✅ Diagnosis Updated")
        st.rerun()  


    st.markdown("---")
    st.subheader("💓 Vital Entry")

    if patient_status != "Discharged":

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            pulse = st.text_input("Pulse")

        with col2:
            bp = st.text_input("BP")

        with col3:
            rr = st.text_input("RR")

        with col4:
            spo2 = st.text_input("SpO₂ (%)")

        with col5:
            temp = st.text_input("Temperature (°C)")

    else:

        st.info("🔒 Vitals Locked (Patient Discharged)")

    if st.button("Save Vitals"):

        os.makedirs(f"Records/{uhid}", exist_ok=True)

        entry = {
            "Date": datetime.now().strftime("%d-%m-%Y"),
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Pulse": pulse,
            "BP": bp,
            "RR": rr,
            "SpO2": spo2,
            "Temperature": temp
        }

        file_exists = os.path.exists(vital_file)

        with open(vital_file, "a", newline="") as f:

            writer = csv.DictWriter(f, fieldnames=entry.keys())

            if not file_exists:
                writer.writeheader()

            writer.writerow(entry)

        st.success("Vitals Saved ✅")
        st.rerun()

    if os.path.exists(vital_file):

        df_vitals = pd.read_csv(vital_file, on_bad_lines='skip')

        st.subheader("Vital History")
        st.dataframe(df_vitals, use_container_width=True)

    st.markdown("---")
    st.subheader("🖼 Upload X-Ray / Images")

    uploaded_files = st.file_uploader(
        "Upload Images (Max 5)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if uploaded_files:

        if len(uploaded_files) > 5:

            st.error("❌ Maximum 5 images allowed")

        else:

            os.makedirs(f"Records/{uhid}/Images", exist_ok=True)

            for file in uploaded_files:

                file_path = f"Records/{uhid}/Images/{file.name}"

                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())

                st.image(file_path, caption=file.name)

            st.success("✅ Images Saved Successfully 😎🔥")

    st.markdown("### 📋 Clinical Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💉 Medication"):
            st.session_state.page = "medication"
            st.rerun()

    with col2:
        if st.button("🦴 OT Notes"):
            st.session_state.page = "ot"
            st.rerun()

    with col3:
        if st.button("📘 OT Register"):
            st.session_state.page = "ot_register"
            st.rerun()

    with col4:
        if st.button("🩸 Blood Transfusion"):
            st.session_state.page = "blood"
            st.rerun()

    st.markdown("---")

    if st.button("🏥 Daycare Surgery", key="patient_daycare_btn"):
        st.session_state.page = "daycare"
        st.rerun()


    if patient_status != "Discharged":

        if st.button("🏥 Discharge Patient"):

            st.session_state.page = "discharge"
            st.rerun()

    # =========================================
# HOSPITAL STAY SUMMARY ROLE CONTROL
# =========================================

    st.markdown("---")
    st.subheader("📘 Hospital Stay Summary")

    status = check_summary_status(uhid)

# DOCTOR → FULL ACCESS
    if st.session_state.get("role") == "Doctor":

        if st.button("📄 Generate Hospital Stay Summary"):

            pdf_path = generate_hospital_summary(uhid)

            if pdf_path:
                show_pdf_preview(pdf_path)

                log_audit(
                    action="HOSPITAL STAY SUMMARY GENERATED (DOCTOR)",
                    user=st.session_state.user,
                    patient=uhid
                )

# NURSE → APPROVAL REQUIRED
    elif st.session_state.get("role") == "Nurse":

        if status != "Approved":

            st.warning("🔒 Approval Required to Generate Summary")

            if st.button("📩 Request Approval from Doctor"):
                request_summary_approval(uhid, "Nurse")
                st.success("Approval Requested")
                st.rerun()

        else:

            if st.button("📄 Generate Hospital Stay Summary"):

                pdf_path = generate_hospital_summary(uhid)

                if pdf_path:
                    show_pdf_preview(pdf_path)

                    log_audit(
                        action="HOSPITAL STAY SUMMARY GENERATED (NURSE)",
                        user=st.session_state.user,
                        patient=uhid
                    )

    # =========================================
# 🩺 DOCTOR ROUND ORDER
# =========================================

    st.markdown("---")
    st.subheader("🩺 Doctor Round Orders")

# File location
    round_file = f"Records/{uhid}/Round_Orders.csv"

# Default values only once
    if "round_time" not in st.session_state:
        st.session_state.round_time = datetime.now().time()

    if "round_date" not in st.session_state:
        st.session_state.round_date = datetime.now().date()

    round_date = st.date_input(
        "Round Date",
        key="round_date"
    )

    round_time = st.time_input(
        "Round Time",
        key="round_time"
    )

    round_note = st.text_area("Enter Round Order")

    if st.button("Save Round Order"):

        entry = {
            "Date": round_date.strftime("%d-%m-%Y"),
            "Time": round_time.strftime("%H:%M:%S"),
            "Doctor": st.session_state.user,
            "Order": round_note
        }

        file_exists = os.path.exists(round_file)

        with open(round_file, "a", newline="") as f:

            writer = csv.DictWriter(
                f,
                fieldnames=["Date","Time","Doctor","Order"]
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(entry)

        st.success("Round Order Saved")

# =========================
# SHOW ROUND HISTORY
# =========================

    if os.path.exists(round_file):

        df_round = pd.read_csv(round_file)

    # Convert to datetime for correct sorting
        df_round["DateTime"] = pd.to_datetime(
            df_round["Date"] + " " + df_round["Time"],
            format="%d-%m-%Y %H:%M:%S"
        )

        df_round = df_round.sort_values(
            by="DateTime",
            ascending=False
        )

        st.subheader("📋 Round History")

    # Group by date
        for date, group in df_round.groupby("Date", sort=False):

            st.markdown(f"### 📅 {date}")

            st.dataframe(
                group[["Time","Doctor","Order"]],
               use_container_width=True
            )  

    if st.button("↩ Back", key="back_discharge"):
        st.session_state.page = "patient_dashboard"
        st.rerun()    

    st.markdown("---")

    if st.button("↩ Back"):
        st.session_state.page = "doctor_dashboard"
        st.rerun()

    if st.button("🚪 Exit"):
        exit_system()
        st.rerun()

elif st.session_state.page == "discharge":

    uhid = st.session_state.selected_patient

    patient_name = load_patient_name(uhid)
    diagnosis = load_latest_diagnosis(uhid)

    admit_date = load_admit_date(uhid)
    discharge_date = datetime.now().strftime("%d-%m-%Y")

    st.title("🏠 Patient Discharge Summary")

    st.info(f"""
    👤 **Patient:** {patient_name}

    🩺 **Diagnosis:** {diagnosis}

    📅 **Admit Date:** {admit_date}

    📅 **Discharge Date:** {discharge_date}
    """)

    st.markdown("---")

    st.subheader("📋 Clinical Details")

    condition_on_discharge = st.selectbox(
        "Condition on Discharge",
        ["Stable", "Improved", "Recovered", "Referred", "Against Medical Advice"]
    )

    discharge_type = st.selectbox(
        "Discharge Type",
        ["Routine", "Daycare", "LAMA", "Absconded", "Death"]
    )

    st.markdown("---")

    st.subheader("📝 Hospital Course")

    hospital_course = st.text_area(
        "Brief Hospital Course",
        placeholder="Enter treatment summary, surgery details, recovery notes...",
        height=120
    )

    st.subheader("💊 Discharge Advice")

    advice = st.text_area(
        "Discharge Advice",
        placeholder="Enter medication advice, precautions, follow-up plan...",
        height=120
    )

    followup_days = st.number_input(
        "Follow-up After (Days)",
        min_value=0,
        step=1
    )

    st.markdown("---")

    if st.button("💾 Save Discharge", key="save_discharge"):

        os.makedirs(f"Records/{uhid}", exist_ok=True)

        summary_file = f"Records/{uhid}/Discharge_Summary.txt"

        with open(summary_file, "w", encoding="utf-8") as f:

            f.write(f"""
PATIENT DISCHARGE SUMMARY
-------------------------

Patient Name: {patient_name}
UHID: {uhid}

Diagnosis: {diagnosis}

Admit Date: {admit_date}
Discharge Date: {discharge_date}

Condition on Discharge: {condition_on_discharge}
Discharge Type: {discharge_type}

Hospital Course:
{hospital_course}

Discharge Advice:
{advice}

Follow-up After: {followup_days} days
""")

        discharge_patient(uhid)

        log_audit(
            action="PATIENT DISCHARGED",
            user=st.session_state.user,
            patient=uhid
        )

        st.success("✅ Discharge Completed Successfully")
        st.session_state.page = "doctor_dashboard"
        st.rerun()

        


    
# =========================================================
# MEDICATION PAGE
# =========================================================

elif st.session_state.page == "medication":

    st.title("💊 Medication Order Sheet")

    uhid = st.session_state.get("selected_patient")

    if not uhid:
        st.error("No patient selected")
        st.stop()

    os.makedirs(f"Records/{uhid}", exist_ok=True)

    order_file = f"Records/{uhid}/Medication_Orders.csv"

    # Load file
    if os.path.exists(order_file):
        df = pd.read_csv(order_file)
    else:
        df = pd.DataFrame(columns=["Date","Time","Doctor","Orders"])

    order_date = st.date_input(
        "Order Date",
        datetime.now(),
        format="DD-MM-YYYY"
    )

    date_str = order_date.strftime("%d-%m-%Y")

    now_time = datetime.now().strftime("%H:%M")

    st.markdown(f"## 📅 {date_str}")

    # =========================
    # COPY PREVIOUS DAY ORDERS
    # =========================

    if st.button("🔁 Copy Previous Day Medicines"):

        if not df.empty:

            prev_orders = df.iloc[-1]["Orders"]

            st.session_state.copy_text = prev_orders

    # =========================
    # ORDER NOTEBOOK
    # =========================

    default_text = st.session_state.get("copy_text","")

    order_text = st.text_area(
        "Doctor Orders",
        value=default_text,
        height=220
    )

    col1,col2 = st.columns(2)

    # Save today's order
    if col1.button("💾 Save Orders"):

        new_row = {
            "Date": date_str,
            "Time": now_time,
            "Doctor": st.session_state.user,
            "Orders": order_text
        }

        df = pd.concat([df,pd.DataFrame([new_row])],ignore_index=True)

        df.to_csv(order_file,index=False)

        st.success("Orders saved")

        st.session_state.copy_text = ""

        st.rerun()

    # Add additional order
    if col2.button("➕ Add Additional Order"):

        new_row = {
            "Date": today,
            "Time": now_time,
            "Doctor": st.session_state.user,
            "Orders": order_text
        }

        df = pd.concat([df,pd.DataFrame([new_row])],ignore_index=True)

        df.to_csv(order_file,index=False)

        st.success("Additional order added")

        st.session_state.copy_text = ""

        st.rerun()

    # =========================
    # SHOW ORDER HISTORY
    # =========================

    st.markdown("---")
    st.subheader("📋 Medication Timeline")

    if not df.empty:

        df = df.sort_values(by=["Date","Time"],ascending=False)

        for i,row in df.iterrows():

            with st.expander(f"📅 {row['Date']} | ⏱ {row['Time']} | {row['Doctor']}"):

                edited = st.text_area(
                    "Orders",
                    row["Orders"],
                    key=f"edit_{i}",
                    height=200
                )


                admin_file = f"Records/{uhid}/Medication_Admin_Log.csv"

                if not os.path.exists(admin_file):
                    df_admin = pd.DataFrame(
                        columns=["Date","Medicine","Dose","Time","Nurse"]
                    )
                    df_admin.to_csv(admin_file,index=False)
                else:
                    df_admin = pd.read_csv(admin_file)

                orders = row["Orders"].split("\n")

                for med in orders:

                    if med.strip() == "":
                        continue

                    col1, col2, col3 = st.columns([6,1,1])

                    col1.write(med)

                    morning = df_admin[
                        (df_admin["Medicine"] == med) &
                        (df_admin["Date"] == row["Date"]) &
                        (df_admin["Dose"] == "Morning")
                    ]

                    evening = df_admin[
                        (df_admin["Medicine"] == med) &
                        (df_admin["Date"] == row["Date"]) &
                        (df_admin["Dose"] == "Evening")
                    ]

                    if not morning.empty:
                        col2.markdown(f"☑ {morning.iloc[-1]['Time']}")
                    else:
                        if col2.button("☐", key=f"morning_{i}_{med}"):

                            now_time = datetime.now().strftime("%H:%M")

                            new_row = {
                                "Date": row["Date"],
                                "Medicine": med,
                                "Dose": "Morning",
                                "Time": now_time,
                                "Nurse": st.session_state.user
                            }

                            df_admin = pd.concat([df_admin,pd.DataFrame([new_row])],ignore_index=True)

                            df_admin.to_csv(admin_file,index=False)

                            st.rerun()

                    if not evening.empty:
                        col3.markdown(f"☑ {evening.iloc[-1]['Time']}")
                    else:
                        if col3.button("☐", key=f"evening_{i}_{med}"):

                            now_time = datetime.now().strftime("%H:%M")

                            new_row = {
                                "Date": row["Date"],
                                "Medicine": med,
                                "Dose": "Evening",
                                "Time": now_time,
                                "Nurse": st.session_state.user
                            }

                            df_admin = pd.concat([df_admin,pd.DataFrame([new_row])],ignore_index=True)

                            df_admin.to_csv(admin_file,index=False)

                            st.rerun()

    st.markdown("---")

    if st.button("⬅ Back", key="med_back"):
        st.session_state.page="patient_dashboard"
        st.rerun()

 

    



#EDIT MEDICATION
elif st.session_state.page == "edit_medication":

    st.title("✏ Edit Medication History")

    uhid = st.session_state.get("selected_patient")

    medication_file = f"Records/{uhid}/Medication_Log.csv"

    if not os.path.exists(medication_file):
        st.warning("No medication records found")
        st.stop()

    df_med = pd.read_csv(
        medication_file,
        on_bad_lines="skip",
        engine="python"
    )

    # =========================
    # ADD NEW MEDICATION ENTRY
    # =========================

    st.subheader("➕ Add Medication Entry")

    if "med_date" not in st.session_state:
        st.session_state.med_date = datetime.now().date()

    med_date = st.date_input(
        "Date",
        key="med_date"
    )
    if "med_time" not in st.session_state:
        st.session_state.med_time = datetime.now().time()

    med_time = st.time_input(
        "Time",
        key="med_time"
    )

    medicine = st.text_input("Medicine Name")
    dose = st.text_input("Dose")
    medicine_type = st.selectbox(
        "Medicine Type",
        [
            "Injection",
            "Tablet",
            "Capsule",
            "Syrup",
            "IV Fluid",
            "Nasal Drop",
            "Eye Drop",
            "Ear Drop",
            "Ointment",
            "Inhaler",
            "Other"
       ]
    )
    route = st.selectbox("Route", ["IV","IM","Oral"])
    frequency = st.selectbox("Frequency", ["OD","BD","TDS","QID","SOS"])

    if st.button("Add Medicine"):

        new_row = {
            "Date": med_date.strftime("%d-%m-%Y"),
            "Time": med_time.strftime("%H:%M:%S"),
            "Medicine Type": medicine_type,
            "Medicine": medicine,
            "Dose": dose,
            "Route": route,
            "Frequency": frequency,
            "Entered_By": st.session_state.user
        }

        df_med = pd.concat([df_med, pd.DataFrame([new_row])], ignore_index=True)

        df_med.to_csv(medication_file, index=False)

        st.success("Medicine added")

        st.rerun()

    # =========================
    # EDIT EXISTING MEDICATION
    # =========================
        st.subheader("💊 Medication Record")

        if os.path.exists(medication_file):

            df_med = pd.read_csv(
                medication_file,
                on_bad_lines="skip",
                engine="python"
            )

    # Create datetime for sorting
            df_med["DateTime"] = pd.to_datetime(
                df_med["Date"] + " " + df_med["Time"],
                format="%d-%m-%Y %H:%M:%S"
            )

            df_med = df_med.sort_values(
                by="DateTime",
                ascending=False
            )

    # Date wise grouping
            for date, group in df_med.groupby("Date", sort=False):

                st.markdown(f"### 📅 {date}")

                for _, row in group.iterrows():

                    med_line = (
                        f"• {row['Medicine']} "
                        f"{row.get('Dose','')} "
                        f"{row.get('Type','')} "
                        f"{row.get('Frequency','')}"
                    )

                    st.write(med_line) 
    

    if st.button("💾 Save Changes"):

        edited_df.to_csv(medication_file, index=False)

        st.success("Medication history updated")
        st.rerun()
    if st.button("⬅ Back", key="med_back1"):

        st.session_state.page = "medication"
        st.rerun()
# =========================================================
# BLOOD TRANSFUSION PAGE
# =========================================================

elif st.session_state.page == "blood":

    uhid = st.session_state.selected_patient

    patient_name = load_patient_name(uhid)
    patient_status = load_patient_status(uhid)

    blood_file = f"Records/{uhid}/Blood_Transfusion_Log.csv"

    st.title("🩸 Blood Transfusion Record")

    st.markdown(f"""
    **Patient:** {patient_name}  
    **UHID:** {uhid}  
    **Date:** {datetime.now().strftime("%d-%m-%Y")}
    """)

    st.markdown("---")

    blood_product = st.selectbox(
        "Blood Product",
        ["PRBC", "Whole Blood", "Platelets", "FFP", "Cryoprecipitate"]
    )

    blood_group = st.selectbox(
        "Blood Group",
        ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    )

    bag_number = st.text_input("Blood Bag Number")

    indication = st.text_area("Indication for Transfusion")

    pre_vitals = st.text_input("Pre-Transfusion Vitals")

    reaction = st.selectbox(
        "Transfusion Reaction",
        ["None", "Fever", "Allergic", "Hemolytic", "Hypotension", "Other"]
    )

    notes = st.text_area("Clinical Notes")

    st.markdown("---")
    st.subheader("🖼 Upload Blood Bag Photo")

    uploaded_photo = st.file_uploader(
        "Upload Blood Bag Image",
        type=["png", "jpg", "jpeg"]
    )

    if patient_status != "Discharged":

        if st.button("💾 Save Transfusion Record"):

            os.makedirs(f"Records/{uhid}", exist_ok=True)

            entry = {
                "Date": datetime.now().strftime("%d-%m-%Y"),
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Product": blood_product,
                "Blood Group": blood_group,
                "Bag Number": bag_number,
                "Indication": indication,
                "Pre Vitals": pre_vitals,
                "Reaction": reaction,
                "Notes": notes
            }

            file_exists = os.path.exists(blood_file)

            with open(blood_file, "a", newline="") as f:

                writer = csv.DictWriter(f, fieldnames=entry.keys())

                if not file_exists:
                    writer.writeheader()

                writer.writerow(entry)

            # ✅ SAVE PHOTO
            if uploaded_photo:

                os.makedirs(f"Records/{uhid}/Blood_Images", exist_ok=True)

                photo_path = f"Records/{uhid}/Blood_Images/{uploaded_photo.name}"

                with open(photo_path, "wb") as f:
                    f.write(uploaded_photo.getbuffer())

                st.image(photo_path, caption="Blood Bag Saved ✅")

            log_audit(
                action="BLOOD TRANSFUSION RECORDED",
                user=st.session_state.user,
                patient=uhid,
                details=blood_product
            )

            st.success("✅ Transfusion Record Saved")
            st.rerun()

    else:
        st.warning("🔒 Transfusion Entry Locked (Patient Discharged)")

    # ✅ SHOW HISTORY

    if os.path.exists(blood_file):

        df_blood = pd.read_csv(blood_file)

        st.markdown("---")
        st.subheader("📋 Transfusion History")

        st.dataframe(df_blood, use_container_width=True)

    if st.button("↩ Back"):
        st.session_state.page = "patient_dashboard"
        st.rerun()




# =========================================================
# DELETE MANAGEMENT PAGE
# =========================================================

elif st.session_state.page == "delete_manage":

    st.title("🗑 Delete Patient Record")

    df_registry = pd.read_csv("Patients_Data.csv", on_bad_lines='skip')
    df_registry["UHID"] = df_registry["UHID"].astype(str)

    selected_patient = st.selectbox(
        "Select Patient",
        df_registry["UHID"]
    )

    st.warning(f"⚠️ You are deleting UHID: {selected_patient}")

    if st.button("❌ Confirm Delete"):


        patient_folder = f"Records/{selected_patient}"
        archive_folder = f"Archive/{selected_patient}"

        os.makedirs("Archive", exist_ok=True)

        if os.path.exists(patient_folder):
            shutil.move(patient_folder, archive_folder)

        df_registry = df_registry[df_registry["UHID"] != selected_patient]
        df_registry.to_csv("Patients_Data.csv", index=False)

        log_audit(
            action="PATIENT RECORD DELETED",
            user=st.session_state.user,
            patient=selected_patient
        )

        st.success("✅ Patient Record Archived")

        st.session_state.page = "doctor_dashboard"
        st.rerun()

    if st.button("↩ Back"):
        st.session_state.page = "doctor_dashboard"
        st.rerun()


# =========================================================
# NEW SMART OT PAGE
# =========================================================

elif st.session_state.page == "ot":
    ot_module()

    if "ai_ot_note" not in st.session_state:
        st.session_state.ai_ot_note = ""

    uhid = st.session_state.selected_patient

    patient_name = load_patient_name(uhid)
    diagnosis_auto = load_latest_diagnosis(uhid)

    st.markdown(f"""
### 🏥 Operative Case Sheet

**Patient Name:** {patient_name}  
**UHID:** {uhid}  
**Diagnosis:** {diagnosis_auto}  
**Date:** {datetime.now().strftime("%d-%m-%Y")}
""")

    st.title("🦴 OT Notes Generator")

    diagnosis = st.text_input(
        "Diagnosis",
        value=diagnosis_auto,
        key="ot_diagnosis"
    )

    surgery_type = st.selectbox(
        "Select Surgery",
        [
            "IMIL Nailing",
            "DHS Fixation",
            "THR",
            "TKR",
            "Arthroscopy",
            "Spine Surgery",   # ✅ FIXED
            "Malleolar Screw Fixation",
            "Proximal Tibia Locking Plate",
            "Forearm Square Nailing",
            "Both Bone Plating",
            "External Fixator",
            "JESS Application",
            "Hemiarthroplasty (AMP Prosthesis)",
            "Skin Grafting",
            "Debridement",
            "K-Wire Fixation",
            "CC Screw Fixation"
        ]
    )

    implant_type = st.selectbox(
        "Implant Used",
        ["None", "Nail", "Plate", "External Fixator", "K-Wire", "Prosthesis"]
    )

    nail_size = ""
    plate_type = ""
    holes = ""

    if implant_type == "Nail":
        nail_size = st.text_input("Nail Size")

    if implant_type == "Plate":
        plate_type = st.selectbox("Plate Type", ["Locking", "Non-Locking"])
        holes = st.text_input("Number of Holes")

    findings = st.text_area("Operative Findings")

    surgeon_name = st.selectbox(
        "Surgeon",
        [
            "DR SIDDHARTH RASTOGI",
            "DR RAJESH RASTOGI"
        ]
    )

    blood_loss = st.selectbox(
        "Estimated Blood Loss (ml)",
        ["Minimal", "50", "100", "200", "500", "More than 500"]
    )

    complications = st.multiselect(
        "Intraoperative Complications",
        ["None", "Bleeding", "Difficulty Reduction", "Implant Issue", "Anaesthesia Issue"]
    )

    if st.button("🧠 Generate AI OT Note"):

        note = generate_ai_ot_note(
            patient_name,
            diagnosis,
            surgery_type + f" using {implant_type}",
            findings + f"\nImplant Details: {nail_size} {plate_type} {holes}"
        )

        st.session_state.ai_ot_note = note
        st.rerun()

    st.markdown("---")
    st.subheader("✍️ Edit Final OT Note")

    edited_note = st.text_area(
        "Final OT Note",
        value=st.session_state.ai_ot_note,
        height=350
    )

    if st.button("💾 Save OT Note", key="save_ot"):

        save_ot_register_entry(
            datetime.now().strftime("%d-%m-%Y"),
            patient_name,
            uhid,
            diagnosis,
            surgery_type,
            implant_type,
            nail_size,
            plate_type,
            holes,
            surgeon_name
        )

        os.makedirs(f"Records/{uhid}", exist_ok=True)

        with open(f"Records/{uhid}/OT_Note.txt", "w", encoding="utf-8") as f:
            f.write(edited_note)

        st.success("✅ OT Note Saved 😎🔥")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👁️ Preview OT Note", key="preview_ot"):

            pdf_path = f"Records/{uhid}/OT_Note.pdf"

            generate_pdf(pdf_path, edited_note.split("\n"))
            show_pdf_preview(pdf_path)

    with col2:
        if st.button("🖨️ Print OT Note", key="print_ot"):

            pdf_path = f"Records/{uhid}/OT_Note.pdf"

            generate_pdf(pdf_path, edited_note.split("\n"))
            st.success("✅ Ready for Printing")

    if st.button("↩ Back", key="ot_back"):
        st.session_state.page = "patient_dashboard"
        st.rerun()




elif st.session_state.page == "ot_register":

    st.title("📘 OT Register")

    if os.path.exists(OT_REGISTER_FILE):

        df_ot = pd.read_csv(OT_REGISTER_FILE, on_bad_lines='skip')

        st.dataframe(df_ot, use_container_width=True)

    else:

        st.info("No OT Entries Yet")

    if st.button("↩ Back", key="ot_register_back"):

        st.session_state.page = "patient_dashboard"
        st.rerun()
elif st.session_state.page == "daycare_register":

    st.title("📘 Day Care Surgery Register")

    if os.path.exists(DAYCARE_REGISTER_FILE):

        df_daycare = pd.read_csv(DAYCARE_REGISTER_FILE)

        if df_daycare.empty:
            st.info("No Day Care Surgeries Recorded Yet")
        else:

            # Show all records
            st.dataframe(df_daycare, use_container_width=True)

            st.markdown("---")
            st.subheader("🔎 View Surgery Details")

            selected_patient = st.selectbox(
                "Select Surgery Record",
                df_daycare["Patient Name"]
            )

        if selected_patient:

            record = df_daycare[
                df_daycare["Patient Name"] == selected_patient
            ].iloc[0]

            records_folder = "DayCare_Records"

            selected_patient = record["Patient Name"]

            matching_files = [
                f for f in os.listdir(records_folder)
                if selected_patient in f
            ]

            if matching_files:

                # Pick latest file if multiple
                matching_files.sort(reverse=True)

                file_path = os.path.join(records_folder, matching_files[0])

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                st.markdown("### 📝 Full Surgery Record")
                st.text(content)

            else:
                st.error("Surgery file not found")

                

    else:
        st.info("No Day Care Surgeries Recorded Yet")

    if st.button("↩ Back", key="daycare_register_back"):
        st.session_state.page = "doctor_dashboard"
        st.rerun()


elif st.session_state.page == "daycare":

    st.title("🏥 Day Care Surgery")

    st.markdown("---")
    st.subheader("🧾 Day Care Case Entry")

    surgery_date = st.date_input("Date", datetime.now())

    patient_name = st.text_input("Patient Name")
    age = st.text_input("Age / Sex")

    diagnosis = st.text_input("Diagnosis")
    procedure = st.text_input("Procedure Performed")

    anaesthesia = st.selectbox(
        "Anaesthesia",
        ["Local", "Regional", "Spinal", "General","Sedation + Local"]
    )

    surgeon = st.text_input("Surgeon")

    findings = st.text_area("Operative Findings")
    notes = st.text_area("Post-Procedure Notes")

    st.markdown("---")

    discharge_advice = st.text_area(
        "Discharge Advice",
        "Patient discharged in stable condition."
    )

    if st.button("💾 Save Day Care Record"):

        if patient_name.strip() == "":
            st.error("❌ Patient Name Required")

        else:

            os.makedirs("DayCare_Records", exist_ok=True)

            file_name = f"DayCare_Records/{patient_name}_{datetime.now().strftime('%H%M%S')}.txt"

            with open(file_name, "w", encoding="utf-8") as f:

                f.write(f"""
DAY CARE SURGERY RECORD
-----------------------

Date: {surgery_date}

Patient Name: {patient_name}
Age / Sex: {age}

Diagnosis:
{diagnosis}

Procedure:
{procedure}

Anaesthesia:
{anaesthesia}

Operative Findings:
{findings}

Post-Procedure Notes:
{notes}

Discharge Advice:
{discharge_advice}

Surgeon:
{surgeon}
""")

            log_audit(
                action="DAY CARE SURGERY RECORDED",
                user=st.session_state.user,
                details=patient_name
            )
            # 🔥 Save to DayCare Register CSV

            entry = {
                "Date": str(surgery_date),
                "Patient Name": patient_name,
                "Age/Sex": age,
                "Diagnosis": diagnosis,
                "Procedure": procedure,
                "Anaesthesia": anaesthesia,
                "Surgeon": surgeon
            }

            df_entry = pd.DataFrame([entry])

            if os.path.exists(DAYCARE_REGISTER_FILE):
                df_entry.to_csv(DAYCARE_REGISTER_FILE, mode='a', header=False, index=False)
            else:
                df_entry.to_csv(DAYCARE_REGISTER_FILE, index=False)
            st.success("✅ Day Care Record Saved 😎🔥")

    



    if st.button("↩ Back to Dashboard"):
        st.session_state.page = "doctor_dashboard"
        st.rerun()
    
   
elif st.session_state.page == "medical_fitness_certificate":

    st.title("📄 Medical & Fitness Certificate")

    st.markdown("### 👤 Patient Details")

    patient_name = st.text_input("Patient Name")
    father_name = st.text_input("Father / Husband Name")
    age = st.text_input("Age")
    address = st.text_area("Residential Address")

    st.markdown("---")
    st.markdown("### 🩺 Medical Details")

    diagnosis = st.text_area(
        "Diagnosis",
        height=100,
        placeholder="Enter diagnosis exactly as required..."
    )

    purpose = st.selectbox(
        "Purpose of Certificate",
        [
            "Sick Leave",
            "Employment",
            "School/College",
            "Sports",
            "Surgery",
            "Travel"
        ]
    )

    rest_required = st.checkbox("Rest Required")

    if rest_required:
        rest_from = st.date_input("Rest From")
        rest_to = st.date_input("Rest To")
    else:
        rest_from = None
        rest_to = None

    remarks = st.text_area("Remarks (Optional)")

    st.markdown("---")

    if st.button("Generate Certificate"):

        if patient_name.strip() == "":
            st.error("Patient Name Required")

        elif father_name.strip() == "":
            st.error("Father / Husband Name Required")

        elif age.strip() == "":
            st.error("Age Required")

        elif address.strip() == "":
            st.error("Address Required")

        elif diagnosis.strip() == "":
            st.error("Diagnosis Required")

        else:
            # 🔥 Auto Doctor Data

            doctor_name = st.session_state.user

            doctor_degree = DOCTOR_DATABASE.get(
                doctor_name,
                {}
            ).get("degree", "MBBS")

            doctor_reg = DOCTOR_DATABASE.get(
                doctor_name,
                {}
            ).get("reg_no", "Registration Not Found")
            
            certificate_id = f"MH-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            today = datetime.now().strftime("%d-%m-%Y")

            if rest_required:
                fitness_statement = f"""
            The patient is advised complete rest from
            {rest_from.strftime('%d-%m-%Y')} to {rest_to.strftime('%d-%m-%Y')}.
            """
            else:
                fitness_statement = """
            The patient is medically examined and found FIT to resume normal duties.
            """

            content = f"""
                          MEDICAL CERTIFICATE
                         

            Certificate No: {certificate_id}
            Date: {today}

            ------------------------------------------------------------

            This is to certify that Mr./Ms. {patient_name},
            S/o / W/o {father_name},
            Age: {age} years,
            Resident of:
            {address}

            was examined at our hospital.

            Clinical Diagnosis:
            {diagnosis}

            Purpose of Issue:
            {purpose}

            Medical Opinion:
            {fitness_statement}

            Remarks:
            {remarks}

           ------------------------------------------------------------

            This certificate is issued on patient request
             

            

            For
            MAHAVEER HOSPITAL & DENTAL CARE PRIVATE LIMITED
            SHAHJAHANPUR, U.P

            (Signature & Seal)
            """

            os.makedirs("Certificates", exist_ok=True)

            pdf_path = f"Certificates/{patient_name}_{today}.pdf"

            generate_pdf(pdf_path, content.split("\n"))

            show_pdf_preview(pdf_path)

            log_audit(
                action="MEDICAL/FITNESS CERTIFICATE ISSUED",
                user=st.session_state.user,
                details=patient_name
            )

            st.success("✅ Certificate Generated Successfully")

    if st.button("↩ Back"):
        st.session_state.page = "reception_dashboard"
        st.rerun()
# =========================================================
# ADMIN DASHBOARD
# =========================================================

elif st.session_state.page == "admin_dashboard":

    st.title("🛡 ADMIN CONTROL PANEL")

    st.markdown(f"Logged in as: **{st.session_state.user}**")
    if st.button("💊 Pharmacy Dashboard"):
        st.session_state.page = "pharmacy_dashboard"
        st.rerun()
    st.markdown("---")
    # =========================================
# 👥 USER MANAGEMENT (ON CLICK)
# =========================================

    if "show_user_mgmt" not in st.session_state:
        st.session_state.show_user_mgmt = False

    if st.button("👥 User Management"):
        st.session_state.show_user_mgmt = not st.session_state.show_user_mgmt

    if st.session_state.show_user_mgmt:
        st.markdown("---")
        st.subheader("👥 User Management")

        try:
            all_users = supabase.table("users").select("*").order("status").execute().data or []
        except Exception as e:
            st.error(f"Could not load users: {e}")
            all_users = []

        pending  = [u for u in all_users if u.get("status") == "Pending"]
        approved = [u for u in all_users if u.get("status") == "Approved"]

        # ── Pending Approvals ────────────────────────────────────────────────
        if pending:
            st.markdown(f"#### ⏳ Pending Approval ({len(pending)})")
            for u in pending:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{u['username']}** — {u['role']}"
                            + (f" *(name: {u.get('name','')})*" if u.get('name') else ""))
                if c2.button("✅ Approve", key=f"appr_{u['username']}"):
                    supabase.table("users").update({"status": "Approved"}) \
                        .eq("username", u["username"]).execute()
                    load_users.clear()
                    st.success(f"Approved: {u['username']}")
                    st.rerun()
                if c3.button("❌ Reject", key=f"rej_{u['username']}"):
                    supabase.table("users").delete() \
                        .eq("username", u["username"]).execute()
                    load_users.clear()
                    st.warning(f"Rejected & removed: {u['username']}")
                    st.rerun()
        else:
            st.success("✅ No pending approvals")

        st.markdown("---")

        # ── Active Users ─────────────────────────────────────────────────────
        st.markdown(f"#### 👥 Active Users ({len(approved)})")

        # Add new user manually
        with st.expander("➕ Add User Manually"):
            nc1, nc2 = st.columns(2)
            new_uname  = nc1.text_input("Username", key="new_uname")
            new_upass  = nc2.text_input("Password", key="new_upass")
            nc3, nc4   = st.columns(2)
            new_name   = nc3.text_input("Full Name", key="new_name")
            new_role   = nc4.selectbox("Role",
                ["Doctor","Nurse","Technician","Reception","Admin"],
                key="new_role")
            if st.button("➕ Add User", key="add_user_btn"):
                if new_uname and new_upass:
                    try:
                        supabase.table("users").insert({
                            "username": new_uname.strip(),
                            "password": new_upass.strip(),
                            "name":     new_name.strip(),
                            "role":     new_role,
                            "status":   "Approved"
                        }).execute()
                        load_users.clear()
                        st.success(f"User '{new_uname}' added.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Username and password required.")

        # List & delete active users
        for u in approved:
            c1, c2, c3 = st.columns([3, 1, 1])
            badge = {"Admin":"🔴","Doctor":"🟢","Nurse":"🟡",
                     "Reception":"🔵","Technician":"🟠"}.get(u["role"],"⚪")
            c1.markdown(f"{badge} **{u['username']}** — {u['role']}")

            # Change role
            roles = ["Doctor","Nurse","Technician","Reception","Admin"]
            new_r = c2.selectbox("", roles,
                index=roles.index(u["role"]) if u["role"] in roles else 0,
                key=f"role_{u['username']}",
                label_visibility="collapsed")
            if new_r != u["role"]:
                supabase.table("users").update({"role": new_r}) \
                    .eq("username", u["username"]).execute()
                load_users.clear()
                st.rerun()

            # Delete (protect admin)
            if u["username"] != "admin":
                if c3.button("🗑", key=f"del_{u['username']}", help="Delete user"):
                    supabase.table("users").delete() \
                        .eq("username", u["username"]).execute()
                    load_users.clear()
                    st.warning(f"Deleted: {u['username']}")
                    st.rerun()
            else:
                c3.markdown("*(protected)*")

        st.markdown("---")

        # ── Clear Login History ───────────────────────────────────────────────
        st.markdown("#### 🧹 Clear Login / Audit History")
        col_a, col_b = st.columns(2)
        if col_a.button("🗑 Clear Audit Trail", key="clear_audit"):
            try:
                supabase.table("audit_trail").delete().neq("id", 0).execute()
                st.success("Audit trail cleared.")
            except Exception as e:
                st.error(f"Error: {e}")
        if col_b.button("🗑 Clear Notifications", key="clear_notif"):
            try:
                supabase.table("notifications").delete().neq("id", 0).execute()
                st.success("Notifications cleared.")
            except Exception as e:
                st.error(f"Error: {e}")
   
    # =========================================
# 📂 SEARCHABLE RECORDS (ADMIN ONLY)
# =========================================

    if "show_records" not in st.session_state:
        st.session_state.show_records = False

    if st.button("📂 Records"):
        st.session_state.show_records = not st.session_state.show_records

    if st.session_state.show_records:

        st.markdown("---")
        st.subheader("📂 Hospital Records Overview")

        search_query = st.text_input("🔎 Search by UHID / Name / Diagnosis")

    # ===============================
    # 🏥 ADMITTED PATIENTS
    # ===============================

        st.markdown("### 🏥 Admitted Patients")

        if os.path.exists("Patients_Data.csv"):

            df_patients = pd.read_csv("Patients_Data.csv", on_bad_lines="skip")

            admitted = df_patients[df_patients["Status"] == "Admitted"]

            if search_query:
                admitted = admitted[
                    admitted.astype(str).apply(
                        lambda row: search_query.lower() in row.to_string().lower(),
                        axis=1
                    )
                ]

            total_admitted = len(admitted)

            st.metric("Total Admitted Patients", total_admitted)

            if total_admitted > 0:
                st.dataframe(admitted, use_container_width=True)
            else:
                st.info("No Matching Admitted Patients")

        else:
           st.warning("Patients_Data.csv not found")

        st.markdown("---")

    # ===============================
    # 🏥 DAY CARE SURGERIES
    # ===============================

        st.markdown("### 🏥 Day Care Surgeries")

        DAYCARE_REGISTER_FILE = "DayCare_Register.csv"

        if os.path.exists(DAYCARE_REGISTER_FILE):

            df_daycare = pd.read_csv(DAYCARE_REGISTER_FILE, on_bad_lines="skip")

            if search_query:
                df_daycare = df_daycare[
                    df_daycare.astype(str).apply(
                        lambda row: search_query.lower() in row.to_string().lower(),
                        axis=1
                    )
                ]

            total_daycare = len(df_daycare)

            st.metric("Total Day Care Surgeries", total_daycare)

            if total_daycare > 0:
                st.dataframe(df_daycare, use_container_width=True)
            else:
                st.info("No Matching Day Care Records")

        else:
            st.warning("DayCare_Register.csv not found")

    st.markdown("---")
    st.subheader("📊 Hospital Statistics")

    if os.path.exists("Patients_Data.csv"):

        df_patients = pd.read_csv("Patients_Data.csv")

        total = len(df_patients)
        admitted = len(df_patients[df_patients["Status"] == "Admitted"])
        discharged = len(df_patients[df_patients["Status"] == "Discharged"])

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Patients", total)
        col2.metric("Currently Admitted", admitted)
        col3.metric("Discharged", discharged)

    st.markdown("---")

    if st.button("🚪 Exit Admin"):
        exit_system()
        st.rerun()
# ✅ ROLE CONTROLLED ACTIONS

if st.session_state.role in ["Admin", "Doctor"]:

    if st.button("↩ Reverse Discharge", key="reverse_dc"):

        reverse_discharge_patient(st.session_state.selected_patient)

        log_audit(
            action="DISCHARGE REVERSED",
            user=st.session_state.user,
            patient=st.session_state.selected_patient
        )

        st.success("✅ Discharge Reversed 😎🔥")

        st.session_state.page = "patient_dashboard"
        st.rerun()
    
        
# =========================================================
# ONLINE APPOINTMENTS
# =========================================================

