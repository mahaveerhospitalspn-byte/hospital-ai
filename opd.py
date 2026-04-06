import streamlit as st
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh
import pandas as pd

from supabase_client import supabase
from opd_documentation import opd_documentation_panel


# ========================================
# LOAD TODAY OPD DATA
# ========================================
@st.cache_data(ttl=10)
def load_today_opd():

    today = str(date.today())

    result = supabase.table("opd_live") \
        .select("*") \
        .eq("date", today) \
        .order("token") \
        .limit(200) \
        .execute()

    return result.data


# ========================================
# RECEPTION PANEL
# ========================================
def opd_reception_panel():

    st_autorefresh(interval=15000)

    st.title("🏥 Live OPD Reception Control")

    rows = load_today_opd()

    # -------------------------------
    # METRICS
    # -------------------------------
    total = len(rows)
    waiting = len([r for r in rows if r["status"] == "Waiting"])
    in_consult = len([r for r in rows if r["status"] == "In Consultation"])
    consulted = len([r for r in rows if r["status"] == "Consulted"])

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total", total)
    col2.metric("Waiting", waiting)
    col3.metric("In Consultation", in_consult)
    col4.metric("Consulted", consulted)

    st.divider()

    # -------------------------------
    # LIVE QUEUE
    # -------------------------------
    st.subheader("📋 Live OPD Queue")

    if rows:

        for r in rows:

            st.write(
                f"🎟 {r['token']} | {r['name']} | "
                f"{r['doctor']} | {r['visit_type']} | {r['status']}"
            )

    else:

        st.info("No Patients Added Yet")


# ========================================
# DOCTOR PANEL
# ========================================
def opd_doctor_panel(doctor_name):

    rows_all = load_today_opd()

    rows = [r for r in rows_all if r["doctor"] == doctor_name]

    # -------------------------------
    # DOCTOR METRICS
    # -------------------------------
    total = len(rows)
    waiting = len([r for r in rows if r["status"] == "Waiting"])
    consulted = len([r for r in rows if r["status"] == "Consulted"])
    new_patients = len([r for r in rows if r["visit_type"] == "New"])
    revisit_patients = len([r for r in rows if r["visit_type"] == "Revisit"])

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total", total)
    col2.metric("Waiting", waiting)
    col3.metric("Consulted", consulted)
    col4.metric("New", new_patients)
    col5.metric("Revisit", revisit_patients)

    st.divider()

    # -------------------------------
    # HOSPITAL TOTAL
    # -------------------------------
    total_hospital = len(rows_all)

    dr_rajesh = len([
        r for r in rows_all
        if r["doctor"] == "DR RAJESH RASTOGI"
    ])

    dr_ruchika = len([
        r for r in rows_all
        if r["doctor"] == "DR RUCHIKA RASTOGI"
    ])

    col4, col5, col6 = st.columns(3)

    col4.metric("Total OPD Today", total_hospital)
    col5.metric("Dr Rajesh", dr_rajesh)
    col6.metric("Dr Ruchika", dr_ruchika)

    st.divider()

    # -------------------------------
    # TABLE
    # -------------------------------
    table_data = []

    for r in rows:

        queue = r["name"] if r["status"] == "Waiting" else ""
        consulted_name = r["name"] if r["status"] == "Consulted" else ""

        table_data.append({

            "Token": r["token"],
            "Waiting": queue,
            "Consulted": consulted_name,
            "Procedure": r.get("procedure_done", "")

        })

    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True
    )

    st.divider()

    # -------------------------------
    # QUEUE CONTROL
    # -------------------------------
    if "open_doc_id" not in st.session_state:

        st.session_state.open_doc_id = None

    for idx, r in enumerate(rows):

        st.markdown(
            f"### 👤 Token {r['token']} | {r['name']} | {r['status']}"
        )

        col1, col2, col3 = st.columns(3)

        # ---------------------------
        # DOCUMENTATION BUTTON
        # ---------------------------
        with col1:

            if st.button(
                "📝 Documentation",
                key=f"doc_{r['id']}"
            ):

                st.session_state.open_doc_id = r["id"]

        # ---------------------------
        # START CONSULT
        # ---------------------------
        with col2:

            if r["status"] == "Waiting":

                if st.button(
                    "▶ Start",
                    key=f"start_{idx}"
                ):

                    supabase.table("opd_live") \
                        .update({

                            "status": "In Consultation",
                            "consult_start": str(datetime.now())

                        }) \
                        .eq("id", r["id"]) \
                        .execute()

                    st.rerun()

        # ---------------------------
        # COMPLETE CONSULT
        # ---------------------------
        with col3:

            if r["status"] == "In Consultation":

                if st.button(
                    "✔ Complete",
                    key=f"finish_{idx}"
                ):

                    supabase.table("opd_live") \
                        .update({

                            "status": "Consulted",
                            "consult_end": str(datetime.now())

                        }) \
                        .eq("id", r["id"]) \
                        .execute()

                    st.session_state.open_doc_id = None

                    st.rerun()

        st.divider()

    # -------------------------------
    # DOCUMENTATION PANEL
    # -------------------------------
    if st.session_state.open_doc_id is not None:

        selected_row = None

        for r in rows:

            if r["id"] == st.session_state.open_doc_id:

                selected_row = r

        if selected_row:

            with st.expander(
                "📝 OPD Documentation",
                expanded=True
            ):

                opd_documentation_panel(selected_row)

    # -------------------------------
    # END OPD BUTTON
    # -------------------------------
    st.markdown("---")

    if st.button("End OPD - Mark All Waiting Consulted"):

        today = str(date.today())

        supabase.table("opd_live") \
            .update({

                "status": "Consulted"

            }) \
            .eq("doctor", doctor_name) \
            .eq("date", today) \
            .eq("status", "Waiting") \
            .execute()

        st.success("All waiting patients marked as Consulted")

        st.rerun()