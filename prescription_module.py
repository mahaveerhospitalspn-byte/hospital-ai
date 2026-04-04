<<<<<<< HEAD
import streamlit as st
import os
from datetime import datetime
import pandas as pd
import os

DRUG_FILE = "drug_database.csv"


def load_drugs():

    if not os.path.exists(DRUG_FILE):

        df = pd.DataFrame({"Drug": []})
        df.to_csv(DRUG_FILE, index=False)

    df = pd.read_csv(DRUG_FILE)

    return df["Drug"].dropna().tolist()


def save_new_drug(drug):

    df = pd.read_csv(DRUG_FILE)

    if drug not in df["Drug"].values:

        new = pd.DataFrame({"Drug": [drug]})
        df = pd.concat([df, new], ignore_index=True)

        df.to_csv(DRUG_FILE, index=False)

# ===============================
# PRESCRIPTION TEMPLATES
# ===============================

TEMPLATES = {

    "Fracture Pain": [
        "Tab Aceclofenac + Paracetamol 1-0-1 x 5 days",
        "Tab Amoxicillin + Clavunic acid 1-0-1 x 5 days",
        "Tab Paracetamol + Tramadol 1/2-0-1/2 x 5 days",
        "Cap Pantoprazole 1-0-0 x 5 days",
        "Tab Calcium Citrate Maleate  0-1-0 x 30 days",
        "Tab Vitamin D weekly x 6 weeks"
    ],

    "Back Pain": [
        "Tab Sulphasalazine 1-0-1 x 5days",
        "tab Iguramolid 0-1-0 x 5 days",
        "Tab Etoricoxib + Thiocochicoside 60/4 1-0-1 x 5 days",
        "Cap Rabeprazole  + levosulpride 1-0-0 x 5 days",
        "Tab Paracetamol + Tramadol 1/2-0-1/2 x 5 days",
        "Hot fomentation"
    ],

    "Knee Pain": [
        "Tab Aceclofenac + PCM 1-0-1 x 5 days",
        "Cap Pantoprazole 1-0-0 x 5 days",
        "Quadriceps exercise"
    ]
}


# ===============================
# PRESCRIPTION PANEL
# ===============================
def prescription_panel(uhid, patient_name):

    st.title("💊 Prescription")

    drugs = load_drugs()

    # number of prescription rows
    if "drug_rows" not in st.session_state:
        st.session_state.drug_rows = 1

    prescription = []

    for i in range(st.session_state.drug_rows):

        st.markdown(f"### • Medicine {i+1}")

        drug = st.selectbox(
            "Drug",
            drugs,
            key=f"drug_{i}"
        )

        dose = st.selectbox(
            "Dose",
            ["1-0-1", "1-0-0", "0-1-0", "0-0-1", "1-1-1", "SOS"],
            key=f"dose_{i}"
        )

        days = st.number_input(
            "Days",
            min_value=1,
            max_value=60,
            step=1,
            key=f"days_{i}"
        )

        prescription.append((drug, dose, days))

        st.divider()

    # Add more drugs
    if st.button("➕ Add Medicine"):
        st.session_state.drug_rows += 1
        st.rerun()

    st.markdown("---")

    advice = st.text_area("Advice")

    if st.button("💾 Save Prescription"):

        folder = f"Records/{uhid}"
        os.makedirs(folder, exist_ok=True)

        file_path = f"{folder}/Prescription.txt"

        with open(file_path, "a", encoding="utf-8") as f:

            f.write("\n\n----- PRESCRIPTION -----\n")
            f.write(f"Patient: {patient_name}\n")
            f.write(f"Date: {datetime.now()}\n\n")

            for drug, dose, days in prescription:
                f.write(f"• {drug}  {dose}  {days} days\n")

            if advice:
                f.write("\nAdvice:\n")
                f.write(advice)

        st.success("Prescription Saved")
=======
import streamlit as st
import os
from datetime import datetime
import pandas as pd
import os

DRUG_FILE = "drug_database.csv"


def load_drugs():

    if not os.path.exists(DRUG_FILE):

        df = pd.DataFrame({"Drug": []})
        df.to_csv(DRUG_FILE, index=False)

    df = pd.read_csv(DRUG_FILE)

    return df["Drug"].dropna().tolist()


def save_new_drug(drug):

    df = pd.read_csv(DRUG_FILE)

    if drug not in df["Drug"].values:

        new = pd.DataFrame({"Drug": [drug]})
        df = pd.concat([df, new], ignore_index=True)

        df.to_csv(DRUG_FILE, index=False)

# ===============================
# PRESCRIPTION TEMPLATES
# ===============================

TEMPLATES = {

    "Fracture Pain": [
        "Tab Aceclofenac + Paracetamol 1-0-1 x 5 days",
        "Tab Amoxicillin + Clavunic acid 1-0-1 x 5 days",
        "Tab Paracetamol + Tramadol 1/2-0-1/2 x 5 days",
        "Cap Pantoprazole 1-0-0 x 5 days",
        "Tab Calcium Citrate Maleate  0-1-0 x 30 days",
        "Tab Vitamin D weekly x 6 weeks"
    ],

    "Back Pain": [
        "Tab Sulphasalazine 1-0-1 x 5days",
        "tab Iguramolid 0-1-0 x 5 days",
        "Tab Etoricoxib + Thiocochicoside 60/4 1-0-1 x 5 days",
        "Cap Rabeprazole  + levosulpride 1-0-0 x 5 days",
        "Tab Paracetamol + Tramadol 1/2-0-1/2 x 5 days",
        "Hot fomentation"
    ],

    "Knee Pain": [
        "Tab Aceclofenac + PCM 1-0-1 x 5 days",
        "Cap Pantoprazole 1-0-0 x 5 days",
        "Quadriceps exercise"
    ]
}


# ===============================
# PRESCRIPTION PANEL
# ===============================
def prescription_panel(uhid, patient_name):

    st.title("💊 Prescription")

    drugs = load_drugs()

    # number of prescription rows
    if "drug_rows" not in st.session_state:
        st.session_state.drug_rows = 1

    prescription = []

    for i in range(st.session_state.drug_rows):

        st.markdown(f"### • Medicine {i+1}")

        drug = st.selectbox(
            "Drug",
            drugs,
            key=f"drug_{i}"
        )

        dose = st.selectbox(
            "Dose",
            ["1-0-1", "1-0-0", "0-1-0", "0-0-1", "1-1-1", "SOS"],
            key=f"dose_{i}"
        )

        days = st.number_input(
            "Days",
            min_value=1,
            max_value=60,
            step=1,
            key=f"days_{i}"
        )

        prescription.append((drug, dose, days))

        st.divider()

    # Add more drugs
    if st.button("➕ Add Medicine"):
        st.session_state.drug_rows += 1
        st.rerun()

    st.markdown("---")

    advice = st.text_area("Advice")

    if st.button("💾 Save Prescription"):

        folder = f"Records/{uhid}"
        os.makedirs(folder, exist_ok=True)

        file_path = f"{folder}/Prescription.txt"

        with open(file_path, "a", encoding="utf-8") as f:

            f.write("\n\n----- PRESCRIPTION -----\n")
            f.write(f"Patient: {patient_name}\n")
            f.write(f"Date: {datetime.now()}\n\n")

            for drug, dose, days in prescription:
                f.write(f"• {drug}  {dose}  {days} days\n")

            if advice:
                f.write("\nAdvice:\n")
                f.write(advice)

        st.success("Prescription Saved")
>>>>>>> d67240b6b301f5efd6ea7b3a00d8b3b998948d69
