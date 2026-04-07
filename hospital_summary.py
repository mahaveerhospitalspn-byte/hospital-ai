
# hospital_summary.py

import os
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch


def generate_hospital_summary(uhid):

    records_folder = f"Records/{uhid}"

    if not os.path.exists(records_folder):
        return None

    info_file = f"{records_folder}/Patient_Info.txt"
    vitals_file = f"{records_folder}/Vitals_Log.csv"
    med_file = f"{records_folder}/Medication_Log.csv"

    patient_name = ""
    diagnosis = ""

    if os.path.exists(info_file):
        with open(info_file, "r", encoding="utf-8") as f:
            content = f.read()

            if "Patient Name:" in content:
                patient_name = content.split("Patient Name:")[1].split("\n")[0].strip()

            if "Diagnosis:" in content:
                diagnosis = content.split("Diagnosis:")[1].split("\n")[0].strip()

    pdf_path = f"{records_folder}/Hospital_Stay_Summary.pdf"

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    x = 1 * inch
    y = height - 2.6 * inch
    line_space = 18

    c.setFont("Helvetica", 12)

    c.drawString(x, y, "HOSPITAL STAY SUMMARY")
    y -= line_space
    c.drawString(x, y, f"Patient Name: {patient_name}")
    y -= line_space
    c.drawString(x, y, f"UHID: {uhid}")
    y -= line_space
    c.drawString(x, y, f"Diagnosis: {diagnosis}")
    y -= line_space * 2

    # Vitals
    if os.path.exists(vitals_file):

        c.drawString(x, y, "Vitals Record:")
        y -= line_space

        df_vitals = pd.read_csv(vitals_file)

        for _, row in df_vitals.iterrows():

            line = f"{row['Date']} | Pulse: {row['Pulse']} | BP: {row['BP']} | RR: {row['RR']}"
            c.drawString(x, y, line)
            y -= line_space

            if y < 2 * inch:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height - 1 * inch

    # Medication
    if os.path.exists(med_file):

        c.showPage()
        c.setFont("Helvetica", 12)
        y = height - 1 * inch

        c.drawString(x, y, "Medication Record:")
        y -= line_space

        df_med = pd.read_csv(med_file)

        for _, row in df_med.iterrows():

            line = f"{row['Date']} | {row['Medicine']} | {row['Dose']} | {row['Route']}"
            c.drawString(x, y, line)
            y -= line_space

            if y < 2 * inch:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height - 1 * inch

    c.save()

    return pdf_path
