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
import pandas as pd

st.cache_data.clear()
st.cache_resource.clear()

st.set_page_config(page_title="Health Tracker", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

# Agentic Logic
doc_parser = DocumentParser.getInstance()
medicine_explainer = MedicineExplainer.getInstance()
pill_identifier = PillIdentifier.getInstance()
conversation = ConversationalInterface.getInstance()

# --- Session State Initialization ---
if "tab" not in st.session_state:
    st.session_state.tab = "dashboard"

# Medication Logic
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

# --- Sidebar (Only on Dashboard) ---
if st.session_state.tab == "dashboard":
    with st.sidebar:
        st.markdown("### Profile Description")
        st.file_uploader("", type=["png", "jpg", "jpeg"])
        full_name = st.text_input("Full Name")
        if full_name:
            st.session_state.first_name = full_name.split()[0] if full_name.strip() else "profile"
        contact = st.text_input("Contact Number")
        email = st.text_input("Email Address")
        consultant = st.text_input("Healthcare Consultant", value="Dr. Sarah Johnson", disabled=True)
        # history = st.text_area("Medical History", placeholder="Enter your medical history, allergies, and current conditions")
        document = st.file_uploader("📎 Upload Medical Documents", type=["pdf", "jpg", "jpeg", "png"], key="med_doc")
        if document:
            response = doc_parser.doc_parser(document, f'{full_name.split()[0]}.json')
            # Parse and store medical history and doctor's note separately
            if response:
                try:
                    data = json.loads(response) if isinstance(response, str) else response
                    st.session_state.uploaded_medical_history = data.get("medical_history", {})
                    st.session_state.uploaded_doctors_note = data.get("doctor's note", "")
                    st.session_state.uploaded_bmi = data.get("bmi", {})
                    st.session_state.uploaded_height = data.get("height", {})
                    st.session_state.uploaded_bp = data.get("bp", {})
                    # st.session_state.first_name = full_name.split()[0] if full_name.strip() else "profile"
                    append_doctor_notes(st.session_state.first_name, st.session_state.uploaded_doctors_note)
                    write_medical_history(st.session_state.first_name, st.session_state.uploaded_medical_history)
                    append_user_stats(st.session_state.first_name, st.session_state.uploaded_bmi, st.session_state.uploaded_height, st.session_state.uploaded_bp)
                    st.write("Medical history, doctor's note, and user information extracted and stored in session state.")
                    st.write(data.get("summary", ""))
                except Exception as e:
                    st.error(f"Failed to parse uploaded document: {e}")
            else:
                st.write("No response from document parser.")

        st.session_state.profile.update({
            "full_name": full_name,
            "contact": contact,
            "email": email,
            "consultant": consultant,
            # "history": history
        })

# --- Dashboard Tab ---
if st.session_state.tab == "dashboard":
    st.title("🌸 Health Tracker Dashboard")
    with open(f'users/{st.session_state.first_name}.json', 'r') as f:
        data = json.load(f)

    col1, col2, col3 = st.columns(3)
    # Prepare data for metrics and charts
    bmi_values = data.get('bmi', [])
    height_values = data.get('height', [])
    bp_values = data.get('bp', [])

    # Convert to DataFrame for plotting if possible
    def to_df(values, label):
        # Accepts list of dicts with 'value' and optional 'date', or just values
        if not values:
            return pd.DataFrame()
        if isinstance(values[0], dict):
            df = pd.DataFrame(values)
            if 'date' in df.columns:
                df = df.sort_values('date')
            if 'value' in df.columns:
                df = df.rename(columns={'value': label})
            return df
        else:
            return pd.DataFrame({label: values})

    bmi_df = to_df(bmi_values, 'BMI')
    height_df = to_df(height_values, 'Height')
    bp_df = to_df(bp_values, 'Blood Pressure')

    metric_style = """
    <style>
    .small-metric .stMetricLabel, .small-metric .stMetricValue {
        font-size: 16px !important;
    }
    </style>
    """
    st.markdown(metric_style, unsafe_allow_html=True)

    with col1:
        with st.container():
            st.markdown('<div class="small-metric">', unsafe_allow_html=True)
            latest_bmi = bmi_df['BMI'].iloc[-1] if not bmi_df.empty else "N/A"
            st.metric("BMI", latest_bmi)
            st.markdown('</div>', unsafe_allow_html=True)
        if not bmi_df.empty:
            st.line_chart(
                bmi_df.set_index('date') if 'date' in bmi_df.columns else bmi_df,
                height=180,
            )
    with col2:
        with st.container():
            st.markdown('<div class="small-metric">', unsafe_allow_html=True)
            latest_height = height_df['Height'].iloc[-1] if not height_df.empty else "N/A"
            st.metric("Height", latest_height)
            st.markdown('</div>', unsafe_allow_html=True)
        if not height_df.empty:
            st.line_chart(
                height_df.set_index('date') if 'date' in height_df.columns else height_df,
                height=180,
            )
    with col3:
        with st.container():
            st.markdown('<div class="small-metric">', unsafe_allow_html=True)
            latest_bp = bp_df['Blood Pressure'].iloc[-1] if not bp_df.empty else "N/A"
            st.metric("Blood Pressure", latest_bp)
            st.markdown('</div>', unsafe_allow_html=True)
        if not bp_df.empty:
            st.line_chart(
                bp_df.set_index('date') if 'date' in bp_df.columns else bp_df,
                height=180,
            )

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
                # --- Sync times before rerun ---
                for j, m in enumerate(st.session_state.medications):
                    tkey = f"time_{j}"
                    if tkey in st.session_state:
                        m["time"] = st.session_state[tkey]
                delete_index = i
                st.session_state.medications.pop(delete_index)
                st.rerun()
        with st.container():
            if st.button("💊 Explain", key=f"explain_{i}"):
                st.session_state[f"show_explain_{i}"] = not st.session_state.get(f"show_explain_{i}", False)
            if st.session_state.get(f"show_explain_{i}", False):
                with st.expander("Medication Explanation", expanded=True):
                    explanation = medicine_explainer.medicine_explainer(med["name"])
                    st.write(explanation)

    # --- Sync times after all UI, before any other rerun ---
    for i, med in enumerate(st.session_state.medications):
        time_key = f"time_{i}"
        if time_key in st.session_state:
            med["time"] = st.session_state[time_key]
    
    st.session_state.missed_medications = []
    st.session_state.current_time = datetime.now()
    for medication in st.session_state.medications:
        if medication["time"] < st.session_state.current_time.time():
            st.session_state.missed_medications.append({"name": medication["name"]})
            print("Added to missed medications!")

    if delete_index is not None:
        st.session_state.medications.pop(delete_index)
        st.rerun()

    if len(st.session_state.missed_medications) != 0:
        with st.expander("Missed medications", expanded=False):
            for i, med in enumerate(st.session_state.missed_medications):
                st.write(med["name"])
                user_question = st.text_input(f"Ask about missed: {med['name']}", key=f"missed_q_{i}")
                if st.button(f"Ask for advice: {med['name']}", key=f"missed_{i}"):
                    if user_question.strip():
                        response = conversation.conversation(f"I missed my {med['name']}. {user_question}")
                        st.info(response)
                    else:
                        response = conversation.conversation(f"I missed my {med['name']}. What should I do?")
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
        if med_hist:
            for entry in med_hist:
                st.markdown(f"- {entry}")
        else:
            st.info("No medical history entries yet.")

        new_entry = st.text_input("Add Medical History Entry")
        if st.button("➕ Add History"):
            write_medical_history(st.session_state.profile["full_name"], new_entry)
            st.success("Added to medical history.")
            st.rerun()

        st.markdown("---")
        st.markdown("**👩‍⚕️ Doctor's Notes**")
        doc_notes = read_doctor_notes(st.session_state.first_name)
        if doc_notes:
            for note in doc_notes:
                st.markdown(f"- {note}")
        else:
            st.info("No doctor notes recorded.")

        new_note = st.text_input("Add Doctor Note")
        if st.button("➕ Add Doctor Note"):
            append_doctor_notes(st.session_state.profile["full_name"], new_note)
            st.success("Doctor note added.")
            st.rerun()
    else:
        st.warning("Please fill out and submit your profile to enable history tracking.")

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
    st.markdown('<div class="insurance-container">', unsafe_allow_html=True)
    st.title("🛡️ Insurance Review")

    provider = st.text_input("Insurance Provider").strip()
    print(provider)
    run_analysis = st.button("Submit Provider")
    insurance_data = None

    if run_analysis and provider.strip():
        with st.spinner("🔍 Running insurance analysis..."):
            context = (
                "User is a 32-year-old freelance graphic designer living in Los Angeles, earning "
                "≈ $85k/year pre-tax with irregular cash-flow, mild asthma, type-2 diabetes family "
                "history, newly married and planning children in ≤ 3 yrs. Needs PPO that covers "
                "Cedars-Sinai + UCLA, strong maternity, fears high deductibles after a $4k ER bill, "
                "values ESG & companies with clean denial records, wants first-class mobile app, "
                "travels abroad ~6×/yr."
            )
            try:
                insurance_data = analyze_insurance(provider, context)
                with open("backend/insurance_analysis_output.json", "w", encoding="utf-8") as f:
                    json.dump(insurance_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                st.error(f"❌ Failed to analyze: {e}")
                insurance_data = None

    if insurance_data:
        st.subheader("📈 Overall Trust Index")
        trust = insurance_data.get("trust_index", 0)
        st.metric(label=f"{provider or 'Selected provider'}", value=f"{trust} / 10")
        st.progress(int(trust * 10))

        st.subheader("🏆 Alternatives (Trust Index)")
        col1, col2 = st.columns(2)
        alts = insurance_data.get("alternatives", [])
        left = alts[: len(alts)//2 + len(alts)%2]
        right = alts[len(left):]

        def render_alt(column, items):
            with column:
                for alt in items:
                    name = alt.get("name", "—")
                    score = alt.get("trust_index", 0)
                    st.markdown(f"**{name}** — {score} / 10")
                    st.progress(int(score * 10))

        render_alt(col1, left)
        render_alt(col2, right)

        st.subheader("💬 Recent Reviews")
        for r in insurance_data.get("reviews", []):
            st.info(f"• {r}")

        st.subheader("📝 Company Background & Controversies")
        desc = insurance_data.get("description", "")
        if isinstance(desc, list):
            desc = "\n".join(desc)
        st.markdown(desc, unsafe_allow_html=True)

        st.subheader("🔗 Supporting Articles")
        for link in insurance_data.get("links", []):
            st.markdown(f"- [{link}]({link})")
    elif run_analysis:
        st.error("Insurance analysis returned no usable data.")

    if st.button("← Back to Dashboard"):
        st.session_state.tab = "dashboard"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- Scan Medication Tab ---
elif st.session_state.tab == "scan":
    st.title("📷 Scan Medication")

    image = st.file_uploader("Upload a medication image", type=["jpg", "jpeg", "png"])
    if image:
        st.image(image, width=300)
        response = pill_identifier.pill_identifier(image)
        st.write(response)
        analysis = medicine_explainer.medicine_explainer(response)
        if isinstance(analysis, dict) and "doctor's note" in analysis:
            try:
                append_doctor_notes(st.session_state.first_name, analysis["doctor's note"])
            except:
                print("Unable to add because no registered user!")
        st.write(analysis)

    if st.button("Analyze Image"):
        st.success("✅ Image analysis complete. (Simulated)")

    if st.button("← Back to Dashboard"):
        st.session_state.tab = "dashboard"
        st.rerun()
