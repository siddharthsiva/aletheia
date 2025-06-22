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

# --- Sidebar (Only on Dashboard) ---
if st.session_state.tab == "dashboard":
    with st.sidebar:
        st.markdown("### Profile Description")
        st.file_uploader("", type=["png", "jpg", "jpeg"])
        full_name = st.text_input("Full Name")
        contact = st.text_input("Contact Number")
        email = st.text_input("Email Address")
        consultant = st.text_input("Healthcare Consultant", value="Dr. Sarah Johnson", disabled=True)
        history = st.text_area("Medical History", placeholder="Enter your medical history, allergies, and current conditions")
        st.file_uploader("📎 Upload Medical Documents", type=["pdf", "jpg", "jpeg", "png"], key="med_doc")

        st.session_state.profile.update({
            "full_name": full_name,
            "contact": contact,
            "email": email,
            "consultant": consultant,
            "history": history
        })

        if st.button("Submit Profile"):
            with open("profile_data.json", "w") as f:
                json.dump(st.session_state.profile, f, indent=4)
            st.session_state.profile_saved = True
            st.success("✅ Profile saved to profile_data.json")

# --- Dashboard Tab ---
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
                delete_index = i
    if delete_index is not None:
        st.session_state.medications.pop(delete_index)
        st.rerun()

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
        med_hist = read_medical_history(st.session_state.profile["full_name"])
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
        doc_notes = read_doctor_notes(st.session_state.profile["full_name"])
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

    provider = st.text_input("Insurance Provider")
    run_analysis = st.button("Submit Provider")
    insurance_data = None

    if run_analysis and provider.strip():
        with st.spinner("🔍 Running Gemini insurance analysis..."):
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

    method = st.radio("Choose input method:", ["Upload Image", "Use Camera"])

    if method == "Upload Image":
        image = st.file_uploader("Upload a medication image", type=["jpg", "jpeg", "png"])
        if image:
            st.image(image, width=300)
            st.success("Image uploaded. (This would be analyzed by backend.)")
    else:
        st.info("Camera access is not supported directly in Streamlit. Please upload a photo instead.")

    if st.button("Analyze Image"):
        st.success("✅ Image analysis complete. (Simulated)")

    if st.button("← Back to Dashboard"):
        st.session_state.tab = "dashboard"
        st.rerun()
