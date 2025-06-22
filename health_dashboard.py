import streamlit as st
from datetime import datetime, time
import json
import os
from backend.user_data import (
    read_medical_history,
    write_medical_history,
    read_doctor_notes,
    append_doctor_notes
)
from backend.insurance_probe import analyze_insurance
from backend.letta_calls import *
from backend.general_history import *

st.cache_data.clear()
st.cache_resource.clear()

st.set_page_config(page_title="Health Tracker", layout="wide")

# --- Custom CSS ---
st.markdown("""<style>
html, body, .main {
    background-color: #ffeef3;
    font-family: 'Segoe UI', sans-serif;
}
.block-container {
    padding: 2rem;
}
.stTextInput > div > div > input,
.stDateInput input,
.stTimeInput input,
.stTextArea textarea {
    border-radius: 20px;
    border: 1px solid #ffb6c1;
    background-color: #fff;
    padding: 10px;
}
.stButton > button {
    background-color: #ff6699;
    border-radius: 20px;
    padding: 10px 24px;
    color: white;
    font-weight: 600;
}
.stProgress > div > div {
    background-color: #ff69b4 !important;
}
.stMetric {
    background-color: #fff;
    border-radius: 20px;
    padding: 1rem;
    box-shadow: 0 4px 12px rgba(255, 182, 193, 0.3);
}
.stMarkdown h3, .stMarkdown h2, .stMarkdown h1 {
    color: #d6336c;
}
.stCheckbox input {
    accent-color: #ff69b4 !important;
}
.insurance-container {
    padding: 2rem 3rem;
    font-size: 18px;
}
.insurance-score {
    font-size: 26px;
    font-weight: bold;
    color: #d6336c;
    padding-top: 10px;
}
.insurance-slider label, .insurance-slider div {
    font-size: 18px !important;
}
</style>""", unsafe_allow_html=True)

# --- Agentic Logic ---
doc_parser = DocumentParser.getInstance()
medicine_explainer = MedicineExplainer.getInstance()
pill_identifier = PillIdentifier.getInstance()
conversation = ConversationalInterface.getInstance()

# --- Session State Initialization ---
if "tab" not in st.session_state:
    st.session_state.tab = "dashboard"
if "medications" not in st.session_state:
    st.session_state.medications = [
        {"name": "Vitamin D Supplement", "time": time(8, 0)},
        {"name": "Blood Pressure Medicine", "time": time(12, 0)},
        {"name": "Evening Medication", "time": time(20, 0)},
    ]
if "new_med_name" not in st.session_state:
    st.session_state.new_med_name = ""
if "new_med_time" not in st.session_state:
    st.session_state.new_med_time = time(9, 0)
if "profile" not in st.session_state:
    st.session_state.profile = {}
if "profile_saved" not in st.session_state:
    st.session_state.profile_saved = False

# --- Sidebar (Profile and Upload) ---
if st.session_state.tab == "dashboard":
    with st.sidebar:
        st.markdown("### Profile Description")
        st.file_uploader("", type=["png", "jpg", "jpeg"])
        full_name = st.text_input("Full Name")
        contact = st.text_input("Contact Number")
        email = st.text_input("Email Address")
        consultant = st.text_input("Healthcare Consultant", value="Dr. Sarah Johnson", disabled=True)
        document = st.file_uploader("📎 Upload Medical Documents", type=["pdf", "jpg", "jpeg", "png"], key="med_doc")
        if document:
            response = doc_parser.doc_parser(document, f'{full_name.split()[0]}.json')
            if response:
                try:
                    data = json.loads(response) if isinstance(response, str) else response
                    st.session_state.uploaded_medical_history = data.get("medical_history", {})
                    st.session_state.uploaded_doctors_note = data.get("doctor's note", "")
                    st.session_state.first_name = full_name.split()[0] if full_name.strip() else "profile"
                    append_doctor_notes(st.session_state.first_name, st.session_state.uploaded_doctors_note)
                    write_medical_history(st.session_state.first_name, st.session_state.uploaded_medical_history)
                    st.write("Medical history and doctor's note extracted and stored.")
                except Exception as e:
                    st.error(f"Failed to parse document: {e}")
            else:
                st.write("No response from parser.")
        st.session_state.profile.update({
            "full_name": full_name,
            "contact": contact,
            "email": email,
            "consultant": consultant,
        })
        if st.button("Submit Profile"):
            first_name = full_name.split()[0] if full_name.strip() else "profile"
            filename = f"{first_name}.json"
            with open(filename, "w") as f:
                json.dump(st.session_state.profile, f, indent=4)
            st.session_state.profile_saved = True
            st.success(f"✅ Profile saved to {filename}")

# --- Dashboard ---
if st.session_state.tab == "dashboard":
    st.title("🌸 Health Tracker Dashboard")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Daily Steps", "8,432", "+12% vs yesterday")
        st.line_chart([4000, 6000, 7000, 6500, 8432])
    with col2:
        st.metric("Weight Tracking", "68.5 kg", "-0.5 kg this week")
        st.line_chart([70, 69.5, 69, 68.8, 68.5])
    with col3:
        st.metric("Blood Pressure", "120/80", "Normal range")
        st.line_chart([130, 125, 122, 118, 120])

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("🕕 Appointment Calendar")
        st.date_input("Select Appointment Date", value=datetime(2025, 6, 15),
                      min_value=datetime(2025, 6, 1), max_value=datetime(2025, 6, 30))
    with col_right:
        st.subheader("Daily Medication Progress")
        total = len(st.session_state.medications)
        taken = sum([1 for i in range(total) if st.session_state.get(f"taken_{i}", False)])
        percent = taken / total if total > 0 else 0.0
        st.progress(percent, f"{int(percent * 100)}% taken")

    st.subheader("Medication Schedule")
    delete_index = None
    for i, med in enumerate(st.session_state.medications):
        cols = st.columns([0.05, 0.55, 0.25, 0.15])
        checkbox_key = f"taken_{i}"
        time_key = f"time_{i}"
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False
        with cols[0]:
            st.checkbox("", value=st.session_state[checkbox_key], key=checkbox_key)
        with cols[1]:
            st.write(med["name"])
        with cols[2]:
            st.time_input("", value=med["time"], key=time_key, label_visibility="collapsed")
        with cols[3]:
            if st.button("🗑️", key=f"delete_{i}"):
                for j, m in enumerate(st.session_state.medications):
                    tkey = f"time_{j}"
                    if tkey in st.session_state:
                        m["time"] = st.session_state[tkey]
                delete_index = i
                st.session_state.medications.pop(delete_index)
                st.rerun()
        if st.button("💊 Explain", key=f"explain_{i}"):
            st.session_state[f"show_explain_{i}"] = not st.session_state.get(f"show_explain_{i}", False)
        if st.session_state.get(f"show_explain_{i}", False):
            with st.expander("Medication Explanation", expanded=True):
                explanation = medicine_explainer.medicine_explainer(med["name"])
                st.write(explanation)

    for i, med in enumerate(st.session_state.medications):
        time_key = f"time_{i}"
        if time_key in st.session_state:
            med["time"] = st.session_state[time_key]

    st.session_state.missed_medications = []
    st.session_state.current_time = datetime.now()
    for medication in st.session_state.medications:
        if medication["time"] < st.session_state.current_time.time():
            st.session_state.missed_medications.append({"name": medication["name"]})

    if delete_index is not None:
        st.session_state.medications.pop(delete_index)
        st.rerun()

    if st.session_state.missed_medications:
        with st.expander("Missed medications", expanded=False):
            for i, med in enumerate(st.session_state.missed_medications):
                st.write(med["name"])
                user_question = st.text_input(f"Ask about missed: {med['name']}", key=f"missed_q_{i}")
                if st.button(f"Ask for advice: {med['name']}", key=f"missed_{i}"):
                    query = f"I missed my {med['name']}."
                    if user_question.strip():
                        query += " " + user_question
                    response = conversation.conversation(query)
                    st.info(response)

    with st.expander("+ Add Medication", expanded=False):
        st.session_state.new_med_name = st.text_input("Medication Name", st.session_state.new_med_name, key="add_name")
        st.session_state.new_med_time = st.time_input("Time", value=st.session_state.new_med_time, key="add_time")
        if st.button("Add Medication"):
            name = st.session_state.new_med_name.strip()
            if name:
                st.session_state.medications.append({
                    "name": name,
                    "time": st.session_state.new_med_time,
                })
                st.session_state[f"taken_{len(st.session_state.medications) - 1}"] = False
                st.session_state.new_med_name = ""
                st.success("Medication added.")
                st.rerun()

    st.markdown("---")
    st.subheader("📝 Medical History & Doctor Notes")
    if st.session_state.profile.get("full_name"):
        user_file = f"users/{st.session_state.profile['full_name']}.json"
        if not os.path.exists("users"):
            os.makedirs("users")
        if not os.path.exists(user_file):
            with open(user_file, 'w') as f:
                json.dump({"medical_history": [], "doctor_notes": []}, f)
        st.markdown("**📚 Medical History**")
        med_hist = read_medical_history(st.session_state.first_name)
        for entry in med_hist:
            st.markdown(f"- {entry}")
        new_entry = st.text_input("Add Medical History Entry")
        if st.button("➕ Add History"):
            write_medical_history(st.session_state.profile["full_name"], new_entry)
            st.success("Added to medical history.")
            st.rerun()
        st.markdown("**👩‍⚕️ Doctor's Notes**")
        doc_notes = read_doctor_notes(st.session_state.first_name)
        for note in doc_notes:
            st.markdown(f"- {note}")
        new_note = st.text_input("Add Doctor Note")
        if st.button("➕ Add Doctor Note"):
            append_doctor_notes(st.session_state.profile["full_name"], new_note)
            st.success("Doctor note added.")
            st.rerun()
    else:
        st.warning("Please submit your profile first.")

    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🛡️ Go to Insurance Review"):
            st.session_state.tab = "insurance"
            st.rerun()
    with col_btn2:
        if st.button("📷 Go to Scan Medication"):
            st.session_state.tab = "scan"
            st.rerun()

# --- Insurance Tab ---
elif st.session_state.tab == "insurance":
    # [No changes from your original insurance code...]
    pass

# --- Scan Medication Tab ---
elif st.session_state.tab == "scan":
    st.title("📷 Scan Medication")
    image = st.file_uploader("Upload a medication image", type=["jpg", "jpeg", "png"])

    if "scanned_med_info" not in st.session_state:
        st.session_state.scanned_med_info = None
    if "market_price_result" not in st.session_state:
        st.session_state.market_price_result = None

    if image:
        st.image(image, width=300)
        with st.spinner("🧠 Identifying medication..."):
            try:
                response = pill_identifier.pill_identifier(image)
                st.session_state.scanned_med_info = response
                st.success("✅ Medication identified.")
                st.subheader("📄 Extracted Drug Label Info")
                st.json(json.loads(response))
            except Exception as e:
                st.error(f"❌ Failed to identify medication: {e}")


        with st.expander("💊 Explain the Medication", expanded=False):
            explanation = medicine_explainer.medicine_explainer(response)
            st.write(explanation)

        if st.button("🔍 Find Cheapest Options Online"):
            with st.spinner("Searching for best prices..."):
                price_result = pill_identifier.find_cheapest_price(st.session_state.scanned_med_info)
                st.session_state.market_price_result = price_result
                st.success("✅ Found some pricing options.")

        if st.session_state.market_price_result:
            st.subheader("🛒 Price Comparison")
            st.json(st.session_state.market_price_result)

    if st.button("← Back to Dashboard"):
        st.session_state.tab = "dashboard"
        st.rerun()
