import streamlit as st
from supabase import create_client
from datetime import date

# ---------------- SUPABASE ----------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- SAVE DUTY ----------------

def save_duty(data):

    supabase.table("staff_duty").insert(data).execute()

# ---------------- LOAD STAFF DUTY ----------------

def load_staff_duty(name, week):

    res = supabase.table("staff_duty") \
        .select("*") \
        .eq("staff_name", name) \
        .eq("week_start", week) \
        .execute()

    return res.data

# ---------------- LOAD ALL DUTIES ----------------

def load_all_duties():

    res = supabase.table("staff_duty") \
        .select("*") \
        .order("week_start", desc=True) \
        .execute()

    return res.data

# ---------------- SAVE ATTENDANCE ----------------

def mark_attendance(name, status):

    data = {
        "staff_name": name,
        "date": str(date.today()),
        "status": status
    }

    supabase.table("attendance").insert(data).execute()

# ---------------- ADMIN PANEL ----------------

def admin_panel():

    st.title("Staff Duty Allocation")

    week = st.date_input("Week Start")

    staff = st.text_input("Staff Name")

    role = st.selectbox("Role", [
        "Nurse",
        "Ward Boy",
        "Reception",
        "OT Staff",
        "Lab"
    ])

    plaster = st.checkbox("Plaster Room")
    opd1 = st.checkbox("OPD 1")
    opd2 = st.checkbox("OPD 2")
    bp = st.checkbox("BP Pulse Station")
    ot = st.checkbox("OT")
    ward = st.checkbox("Ward")

    if st.button("Save Duty"):

        save_duty({
            "staff_name": staff,
            "role": role,
            "week_start": str(week),

            "plaster": plaster,
            "opd1": opd1,
            "opd2": opd2,
            "bp_station": bp,
            "ot": ot,
            "ward": ward
        })

        st.success("Saved")

# ---------------- STAFF VIEW ----------------

def staff_view(name):

    st.title("My Duty This Week")

    week = st.date_input("Select Week")

    duties = load_staff_duty(name, str(week))

    if duties:

        d = duties[0]

        table = {
            "Department":[
                "Plaster Room",
                "OPD 1",
                "OPD 2",
                "BP Pulse Station",
                "OT",
                "Ward"
            ],
            "Assigned":[
                d["plaster"],
                d["opd1"],
                d["opd2"],
                d["bp_station"],
                d["ot"],
                d["ward"]
            ]
        }

        st.table(table)

    else:

        st.warning("No duty assigned")

    st.subheader("Mark Attendance")

    status = st.selectbox("Status", [
        "Present",
        "Absent",
        "Leave"
    ])

    if st.button("Submit Attendance"):

        mark_attendance(name, status)

        st.success("Attendance saved")

# ---------------- DOCTOR VIEW ----------------

def doctor_view():

    st.title("All Staff Duties")

    data = load_all_duties()

    st.dataframe(data)

# ---------------- LOGIN ----------------

def main():

    st.sidebar.title("Login")

    role = st.sidebar.selectbox("Login As", [
        "Admin",
        "Doctor",
        "Staff"
    ])

    name = st.sidebar.text_input("Name")

    if role == "Admin":

        admin_panel()

    elif role == "Doctor":

        doctor_view()

    elif role == "Staff":

        staff_view(name)


main()