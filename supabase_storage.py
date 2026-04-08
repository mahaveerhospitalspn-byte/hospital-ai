"""
supabase_storage.py
===================
Drop-in replacement for all local file I/O in app.py.
Run the SQL in create_supabase_tables.sql in your Supabase dashboard FIRST.

Every function mirrors the original file-based API so app.py changes are minimal.
"""

import os
import json
from datetime import datetime
from supabase_client import supabase


# ─── PATIENTS ────────────────────────────────────────────────────────────────

def register_patient_sb(uhid, patient_name, diagnosis, admitted_on,
                         age="", gender="", address="", mobile=""):
    """Insert or update a patient record in Supabase."""
    supabase.table("patients").upsert({
        "uhid":        str(uhid),
        "name":        patient_name.strip().upper(),
        "diagnosis":   diagnosis.strip(),
        "status":      "Admitted",
        "admitted_on": str(admitted_on),
        "age":         str(age),
        "gender":      str(gender),
        "address":     str(address),
        "mobile":      str(mobile),
    }).execute()


def load_patient_info_sb(uhid):
    """Return patient info dict or None."""
    r = supabase.table("patients").select("*").eq("uhid", str(uhid)).execute()
    return r.data[0] if r.data else None


def load_patient_name_sb(uhid):
    info = load_patient_info_sb(uhid)
    return info["name"] if info else str(uhid)


def load_patient_status_sb(uhid):
    info = load_patient_info_sb(uhid)
    return info["status"] if info else "Unknown"


def discharge_patient_sb(uhid, condition="", discharge_type="",
                          instructions="", follow_up=""):
    """Mark patient as discharged and save discharge info."""
    supabase.table("patients").update({
        "status":           "Discharged",
        "discharged_on":    datetime.now().strftime("%d-%m-%Y"),
        "discharge_condition": condition,
        "discharge_type":   discharge_type,
        "discharge_instructions": instructions,
        "follow_up":        follow_up,
    }).eq("uhid", str(uhid)).execute()


def reverse_discharge_sb(uhid):
    supabase.table("patients").update({"status": "Admitted"}) \
        .eq("uhid", str(uhid)).execute()


def get_admitted_patients_sb():
    """Return list of admitted patient dicts."""
    r = supabase.table("patients") \
        .select("uhid,name,diagnosis,status,admitted_on") \
        .eq("status", "Admitted") \
        .order("admitted_on", desc=True) \
        .execute()
    return r.data or []


def load_patient_registry_sb():
    """Return all patients as list of dicts."""
    r = supabase.table("patients").select("*").execute()
    return r.data or []


def patient_exists_sb(uhid):
    r = supabase.table("patients").select("uhid").eq("uhid", str(uhid)).execute()
    return len(r.data) > 0


# ─── VITALS ──────────────────────────────────────────────────────────────────

def save_vitals_sb(uhid, pulse, bp, rr, spo2="", temp="", source="Manual"):
    supabase.table("vitals").insert({
        "uhid":   str(uhid),
        "date":   datetime.now().strftime("%d-%m-%Y"),
        "time":   datetime.now().strftime("%H:%M:%S"),
        "pulse":  str(pulse),
        "bp":     str(bp),
        "rr":     str(rr),
        "spo2":   str(spo2),
        "temp":   str(temp),
        "source": source,
    }).execute()


def load_vitals_sb(uhid):
    """Return list of vital records for patient."""
    r = supabase.table("vitals").select("*") \
        .eq("uhid", str(uhid)) \
        .order("date", desc=False) \
        .execute()
    return r.data or []


def vitals_done_today_sb(uhid):
    today = datetime.now().strftime("%d-%m-%Y")
    r = supabase.table("vitals").select("id") \
        .eq("uhid", str(uhid)).eq("date", today).execute()
    return len(r.data) > 0


# ─── MEDICATIONS ─────────────────────────────────────────────────────────────

def save_medication_sb(uhid, medicine, dose, route, frequency, given_by=""):
    supabase.table("medications").insert({
        "uhid":      str(uhid),
        "date":      datetime.now().strftime("%d-%m-%Y"),
        "time":      datetime.now().strftime("%H:%M:%S"),
        "medicine":  medicine,
        "dose":      dose,
        "route":     route,
        "frequency": frequency,
        "given_by":  given_by,
    }).execute()


def load_medications_sb(uhid):
    r = supabase.table("medications").select("*") \
        .eq("uhid", str(uhid)) \
        .order("date", desc=False) \
        .execute()
    return r.data or []


def meds_done_today_sb(uhid):
    today = datetime.now().strftime("%d-%m-%Y")
    r = supabase.table("medications").select("id") \
        .eq("uhid", str(uhid)).eq("date", today).execute()
    return len(r.data) > 0


# ─── NURSING NOTES ───────────────────────────────────────────────────────────

def save_nursing_note_sb(uhid, note, nurse=""):
    supabase.table("nursing_notes").insert({
        "uhid":      str(uhid),
        "date":      datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "note":      note,
        "nurse":     nurse,
    }).execute()


def load_nursing_notes_sb(uhid):
    r = supabase.table("nursing_notes").select("*") \
        .eq("uhid", str(uhid)).order("date").execute()
    return r.data or []


# ─── OT NOTES ────────────────────────────────────────────────────────────────

def save_ot_note_sb(uhid, note_text, surgeon="", procedure="", date_of_surgery=""):
    supabase.table("ot_notes").upsert({
        "uhid":            str(uhid),
        "note":            note_text,
        "surgeon":         surgeon,
        "procedure":       procedure,
        "date_of_surgery": str(date_of_surgery),
        "created_at":      datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    }).execute()


def load_ot_note_sb(uhid):
    r = supabase.table("ot_notes").select("*").eq("uhid", str(uhid)).execute()
    return r.data[0] if r.data else None


def ot_done_sb(uhid):
    r = supabase.table("ot_notes").select("id").eq("uhid", str(uhid)).execute()
    return len(r.data) > 0


# ─── DIAGNOSIS ───────────────────────────────────────────────────────────────

def save_diagnosis_sb(uhid, diagnosis):
    supabase.table("patients").update({"diagnosis": diagnosis}) \
        .eq("uhid", str(uhid)).execute()


def load_latest_diagnosis_sb(uhid):
    info = load_patient_info_sb(uhid)
    return info["diagnosis"] if info else "General Case"


# ─── OT REGISTER ─────────────────────────────────────────────────────────────

def save_ot_register_sb(date, patient_name, uhid, diagnosis,
                         surgery, implant, nail_size, plate_type, holes, surgeon):
    supabase.table("ot_register").insert({
        "date":         str(date),
        "patient_name": patient_name,
        "uhid":         str(uhid),
        "diagnosis":    diagnosis,
        "surgery":      surgery,
        "implant":      implant,
        "nail_size":    nail_size,
        "plate_type":   plate_type,
        "holes":        str(holes),
        "surgeon":      surgeon,
    }).execute()


def load_ot_register_sb():
    r = supabase.table("ot_register").select("*").order("date", desc=True).execute()
    return r.data or []


# ─── DAYCARE REGISTER ────────────────────────────────────────────────────────

def save_daycare_sb(date, patient_name, diagnosis, procedure, surgeon):
    supabase.table("daycare_register").insert({
        "date":         str(date),
        "patient_name": patient_name,
        "diagnosis":    diagnosis,
        "procedure":    procedure,
        "surgeon":      surgeon,
    }).execute()


def load_daycare_register_sb():
    r = supabase.table("daycare_register").select("*").order("date", desc=True).execute()
    return r.data or []


# ─── BLOOD PRODUCTS ──────────────────────────────────────────────────────────

def save_blood_product_sb(uhid, product, blood_group, units, reaction, given_by):
    supabase.table("blood_products").insert({
        "uhid":        str(uhid),
        "date":        datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "product":     product,
        "blood_group": blood_group,
        "units":       units,
        "reaction":    reaction,
        "given_by":    given_by,
    }).execute()


def load_blood_products_sb(uhid):
    r = supabase.table("blood_products").select("*").eq("uhid", str(uhid)).execute()
    return r.data or []


# ─── AUDIT TRAIL ─────────────────────────────────────────────────────────────

def log_audit_sb(action, user="", patient="", details=""):
    supabase.table("audit_trail").insert({
        "time":    datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "user":    user,
        "patient": str(patient),
        "action":  action,
        "details": details,
    }).execute()


# ─── NOTIFICATIONS ───────────────────────────────────────────────────────────

def add_notification_sb(message, user="", patient=""):
    supabase.table("notifications").insert({
        "time":    datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "message": message,
        "user":    user,
        "patient": str(patient),
        "seen":    False,
    }).execute()


def get_unseen_notifications_sb(limit=5):
    r = supabase.table("notifications").select("*") \
        .eq("seen", False).order("time", desc=True).limit(limit).execute()
    return r.data or []


def mark_notifications_seen_sb():
    supabase.table("notifications").update({"seen": True}).eq("seen", False).execute()


# ─── SUMMARY APPROVALS ───────────────────────────────────────────────────────

def request_summary_approval_sb(uhid, requested_by):
    supabase.table("summary_approvals").insert({
        "uhid":         str(uhid),
        "requested_by": requested_by,
        "status":       "Pending",
    }).execute()


def check_summary_status_sb(uhid):
    r = supabase.table("summary_approvals").select("status") \
        .eq("uhid", str(uhid)).order("id", desc=True).limit(1).execute()
    return r.data[0]["status"] if r.data else None


def approve_summary_sb(uhid):
    supabase.table("summary_approvals").update({"status": "Approved"}) \
        .eq("uhid", str(uhid)).execute()


# ─── USERS ───────────────────────────────────────────────────────────────────

def load_users_sb():
    r = supabase.table("users").select("*").execute()
    return r.data or []


def approve_user_sb(username):
    supabase.table("users").update({"status": "Approved"}) \
        .eq("username", username).execute()


def save_user_sb(username, password, role):
    supabase.table("users").insert({
        "username": username.strip(),
        "password": password.strip(),
        "role":     role,
        "status":   "Pending",
    }).execute()
