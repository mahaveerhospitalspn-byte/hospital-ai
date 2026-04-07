
import streamlit as st
import datetime
import os
import requests

# =====================
# GROQ API KEY
# =====================

GROQ_API_KEY = "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"


# =====================
# LOAD PATIENT DATA
# =====================

def load_patient_data(uhid):

    file_path = f"Records/{uhid}/Patient_Info.txt"

    data = {
        "name":"",
        "age":"",
        "sex":"Male",
        "diagnosis":""
    }

    if os.path.exists(file_path):

        with open(file_path,"r",encoding="utf-8") as f:

            for line in f.readlines():

                if "Patient Name:" in line:
                    data["name"] = line.replace("Patient Name:","").strip()

                if "Age:" in line:
                    data["age"] = line.replace("Age:","").strip()

                if "Gender:" in line:
                    data["sex"] = line.replace("Gender:","").strip()

                if "Diagnosis:" in line:
                    data["diagnosis"] = line.replace("Diagnosis:","").strip()

    return data


# =====================
# AUTO APPROACH
# =====================

def auto_select_approach(procedure):

    if not procedure:
        return ""

    p = procedure.lower()

    if "pfn" in p or "proximal femoral nail" in p:
        return "Lateral approach to proximal femur"

    elif "dhs" in p or "dynamic hip screw" in p:
        return "Lateral approach to proximal femur"

    elif "interlocking femur" in p or "im nail femur" in p:
        return "Piriformis entry approach"

    elif "tibia nail" in p or "interlocking tibia" in p or "im nail tibia" in p:
        return "Patellar tendon splitting approach"

    elif "distal radius" in p or "radius plate" in p:
        return "Volar Henry approach"

    elif "both bone forearm" in p:
        return "Henry approach for radius and subcutaneous ulna approach"

    elif "humerus" in p:
        return "Deltopectoral approach"

    elif "hemiarthroplasty" in p or "bipolar" in p:
        return "Posterior Moore approach"

    elif "patella" in p:
        return "Anterior midline approach"

    elif "external fixator" in p:
        return "Percutaneous pin insertion technique"

    else:
        return "Standard surgical approach"


# =====================
# GROQ AI CALL
# =====================

def generate_ai_note(prompt):

    try:

        response = requests.post(

            "https://api.groq.com/openai/v1/chat/completions",

            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },

            json={
                "model": "llama3-8b-8192",
                "messages":[
                    {"role":"user","content":prompt}
                ]
            },

            timeout=60
        )

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except:

        return None


# =====================
# PDF SAVE
# =====================

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def generate_pdf(note_text, filename):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(

        Paragraph(
            "<b>MAHAVEER HOSPITAL AND DENTAL CARE PVT LTD</b>",
            styles["Title"]
        )
    )

    elements.append(Spacer(1,0.3*inch))

    elements.append(
        Preformatted(note_text,styles["Normal"])
    )

    doc.build(elements)


# =====================
# MAIN MODULE
# =====================

def ot_module():

    st.title("Orthopedic OT Notes AI")

    selected_uhid = st.session_state.get("selected_patient","")

    auto_data = load_patient_data(selected_uhid)

    st.header("Patient Details")

    col1,col2,col3 = st.columns(3)


    with col1:

        patient_name = st.text_input(
            "Patient Name",
            value=auto_data["name"],
            key="ot_name"
        )

        age = st.text_input(
            "Age",
            value=auto_data["age"],
            key="ot_age"
        )

        sex = st.selectbox(
            "Sex",
            ["Male","Female"],
            key="ot_sex"
        )


    with col2:

        uhid = st.text_input(
            "UHID",
            value=selected_uhid,
            key="ot_uhid"
        )

        date_of_surgery = st.date_input(
            "Date of Surgery",
            value=datetime.date.today(),
            key="ot_date"
        )

        diagnosis = st.text_input(
            "Diagnosis",
            value=auto_data["diagnosis"],
            key="ot_diag"
        )


    with col3:

        # =====================
# SURGEON DROPDOWN
# =====================

        surgeon_list = [

            "DR SIDDHARTH RASTOGI",

            "DR RAJESH RASTOGI",

            "DR AMIT SHARMA",

            "DR VIKAS GUPTA",

            "OTHER"

        ]


        selected_surgeon = st.selectbox(

            "Primary Surgeon",

            surgeon_list,

            key="ot_surgeon_select"
        )


        if selected_surgeon == "OTHER":

            surgeon = st.text_input(

                "Enter Surgeon Name",

                key="ot_custom_surgeon"

            )

        else:

            surgeon = selected_surgeon

        co_surgeon_list = [

            "",

            "DR SIDDHARTH RASTOGI",

            "DR RAJESH RASTOGI",

            "DR AMIT SHARMA",

            "OTHER"

        ]


        selected_co = st.selectbox(

            "Co Surgeon",

            co_surgeon_list,

            key="ot_cosurgeon_select"
        )


        if selected_co == "OTHER":

            co_surgeon = st.text_input(

                "Enter Co Surgeon",

                key="ot_custom_cosurgeon"

        )

        else:

            co_surgeon = selected_co

        anesthetist = st.text_input(
            "Anesthetist",
            key="ot_anesthetist"
        )


    st.header("Surgical Details")

    procedure = st.text_input(
        "Procedure",
        key="ot_proc"
    )

    if procedure:

        st.session_state.ot_approach = auto_select_approach(procedure)

# show editable approach
    approach = st.text_input(

        "Surgical Approach",

        key="ot_approach"

    ) 


    # =====================
    # IMPLANT DROPDOWN
    # =====================

    implant_list = [

        "3.5 mm DCP Plate",

        "4.5 mm LCP Plate",

        "PFN Nail",

        "Interlocking Nail",

        "Hemiarthroplasty",

        "TBW",

        "External Fixator",

        "Cannulated Screw",

        "Other"

    ]


    selected_implant = st.selectbox(

        "Select Implant",

        implant_list,

        key="ot_implant_select"
    )


    if selected_implant == "Other":

        implant = st.text_input(

            "Enter Implant Name",

            key="ot_implant_custom"
        )

    else:

        implant = selected_implant


    findings = st.text_area(

        "Operative Findings",

        key="ot_findings"
    )


    blood_loss = st.text_input(

        "Blood Loss",

        key="ot_blood"
    )


    complications = st.text_input(

        "Complications",

        key="ot_comp"
    )


    note_type = st.radio(

        "Select Note Format",

        ["Short","Detailed"],

        key="ot_note_type"
    )


    # =====================
    # GENERATE NOTE
    # =====================

    if st.button("Generate OT Note", key="generate_ot"):


        if note_type == "Short":

            prompt = f"""

Write concise professional Orthopedic Operative Note.

Diagnosis:
{diagnosis}

Procedure:
{procedure}

Surgical Approach:
{approach}

Implant:
{implant}

Findings:
{findings}

Blood loss:
{blood_loss}

Include consent, anesthesia, aseptic precautions, fixation and stable condition.

"""


        else:

            prompt = f"""

Generate detailed medico-legal Orthopedic Operative Note.

Use senior consultant level surgical language.

Patient identity confirmed.

Informed written consent obtained.

Operative site marked.

Patient shifted to operation theatre.

Adequate anesthesia administered.

Patient positioned carefully with padding.

Part painted and draped in strict aseptic precautions.

Standard surgical approach used:
{approach}

Careful soft tissue dissection performed.

Fracture fragments exposed clearly.

Fracture reduced anatomically.

Internal fixation performed using:
{implant}

Alignment and rotation restored satisfactorily.

Implant position confirmed under fluoroscopy guidance.

Construct stability checked intraoperatively.

Thorough saline wash given.

Meticulous hemostasis achieved.

Layer wise closure performed.

Sterile dressing applied.

Distal neurovascular status confirmed normal.

Patient tolerated procedure well.

Shifted to recovery room in stable condition.

Clinical details:

Diagnosis:
{diagnosis}

Procedure:
{procedure}

Findings:
{findings}

Blood loss:
{blood_loss}

Complications:
{complications}

Write 150 words professional paragraph.

"""


        ai_text = generate_ai_note(prompt)


        if not ai_text:

            ai_text = "AI generation failed. Check internet connection."


        header = f"""

PATIENT NAME:
{patient_name}

AGE/SEX:
{age}/{sex}

UHID:
{uhid}

DATE:
{date_of_surgery}

SURGEON:
Dr {surgeon}

"""


        final_note = header + "\n" + ai_text


        st.session_state.generated_note = final_note


    # =====================
    # EDITABLE NOTE
    # =====================

    if "generated_note" in st.session_state:


        st.subheader("Editable OT Note")

        edited_note = st.text_area(

            "Edit Note",

            st.session_state.generated_note,

            height=400,

            key="ot_edit_box"
        )


        if st.button("Save PDF", key="save_ot_pdf"):


            folder = "ot_notes"

            os.makedirs(folder,exist_ok=True)


            filename = f"{folder}/{patient_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"


            generate_pdf(edited_note,filename)


            st.success("PDF Saved Successfully")



import streamlit as st
import datetime
import os
import requests

# =====================
# GROQ API KEY
# =====================

GROQ_API_KEY = "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"


# =====================
# LOAD PATIENT DATA
# =====================

def load_patient_data(uhid):

    file_path = f"Records/{uhid}/Patient_Info.txt"

    data = {
        "name":"",
        "age":"",
        "sex":"Male",
        "diagnosis":""
    }

    if os.path.exists(file_path):

        with open(file_path,"r",encoding="utf-8") as f:

            for line in f.readlines():

                if "Patient Name:" in line:
                    data["name"] = line.replace("Patient Name:","").strip()

                if "Age:" in line:
                    data["age"] = line.replace("Age:","").strip()

                if "Gender:" in line:
                    data["sex"] = line.replace("Gender:","").strip()

                if "Diagnosis:" in line:
                    data["diagnosis"] = line.replace("Diagnosis:","").strip()

    return data


# =====================
# AUTO APPROACH
# =====================

def auto_select_approach(procedure):

    if not procedure:
        return ""

    p = procedure.lower()

    if "pfn" in p or "proximal femoral nail" in p:
        return "Lateral approach to proximal femur"

    elif "dhs" in p or "dynamic hip screw" in p:
        return "Lateral approach to proximal femur"

    elif "interlocking femur" in p or "im nail femur" in p:
        return "Piriformis entry approach"

    elif "tibia nail" in p or "interlocking tibia" in p or "im nail tibia" in p:
        return "Patellar tendon splitting approach"

    elif "distal radius" in p or "radius plate" in p:
        return "Volar Henry approach"

    elif "both bone forearm" in p:
        return "Henry approach for radius and subcutaneous ulna approach"

    elif "humerus" in p:
        return "Deltopectoral approach"

    elif "hemiarthroplasty" in p or "bipolar" in p:
        return "Posterior Moore approach"

    elif "patella" in p:
        return "Anterior midline approach"

    elif "external fixator" in p:
        return "Percutaneous pin insertion technique"

    else:
        return "Standard surgical approach"


# =====================
# GROQ AI CALL
# =====================

def generate_ai_note(prompt):

    try:

        response = requests.post(

            "https://api.groq.com/openai/v1/chat/completions",

            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },

            json={
                "model": "llama3-8b-8192",
                "messages":[
                    {"role":"user","content":prompt}
                ]
            },

            timeout=60
        )

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except:

        return None


# =====================
# PDF SAVE
# =====================

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def generate_pdf(note_text, filename):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(

        Paragraph(
            "<b>MAHAVEER HOSPITAL AND DENTAL CARE PVT LTD</b>",
            styles["Title"]
        )
    )

    elements.append(Spacer(1,0.3*inch))

    elements.append(
        Preformatted(note_text,styles["Normal"])
    )

    doc.build(elements)


# =====================
# MAIN MODULE
# =====================
