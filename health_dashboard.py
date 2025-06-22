import streamlit as st
from datetime import datetime, time

st.cache_data.clear()
st.cache_resource.clear()

st.set_page_config(page_title="Health Tracker", layout="wide")

# Inject pink-and-white-only CSS
st.markdown("""<style>
html, body, .main { background-color: #ffe6f0; color: #333; font-family: 'Segoe UI', sans-serif; }
div[data-testid="stSidebar"] { background-color: #fff0f5 !important; color: #333; }
.stTextInput > div > div > input, .stTextArea textarea, .stDateInput input, .stTimeInput input {
    border-radius: 10px; border: 1px solid #ffc0cb; background-color: #ffffff !important; color: #333;
}
.stButton > button { background-color: #ff99b6 !important; color: white !important; border: none;
    padding: 10px 20px; border-radius: 8px; }
.stProgress > div > div { background-color: #ff69b4 !important; }
.stMetric { background-color: #fff !important; border-radius: 12px; padding: 16px;
    box-shadow: 0 2px 6px rgba(255,182,193,0.3); }
.st-c7, .st-bv, .st-bz, .st-ca { color: #d6336c !important; }
.block-container { padding: 2rem 2rem; }
.stCheckbox input { accent-color: #ff69b4 !important; }
.stSlider > div > div > div { background: #ffb6c1 !important; }
hr { border: none; border-top: 1px solid #ffb6c1; }
</style>""", unsafe_allow_html=True)

# Session state setup
if "medications" not in st.session_state:
    st.session_state.medications = [
        {"name": "Vitamin D Supplement", "time": time(8, 0)},
        {"name": "Blood Pressure Medicine", "time": time(12, 0)},
        {"name": "Evening Medication", "time": time(20, 0)},
    ]
    for i in range(len(st.session_state.medications)):
        st.session_state[f"taken_{i}"] = False

if "new_med_name" not in st.session_state:
    st.session_state.new_med_name = ""
if "new_med_time" not in st.session_state:
    st.session_state.new_med_time = time(9, 0)

# Sidebar
with st.sidebar:
    st.title("👩‍⚕️ Profile Info")
    st.file_uploader("📸 Add Photo", type=["png", "jpg", "jpeg"])
    full_name = st.text_input("Full Name")
    contact_number = st.text_input("Contact Number")
    email = st.text_input("Email Address")
    st.text_input("Healthcare Consultant", value="Dr. Sarah Johnson", disabled=True)
    st.text_area("Medical History", placeholder="Enter your medical history, allergies, and current conditions")
    doc = st.file_uploader("📎 Upload Medical Documents", type=["pdf", "jpg", "jpeg", "png"], key="med_doc")
    if doc:
        st.success(f"Uploaded: {doc.name}")

# Main Dashboard
st.title("🌸 Health Tracker Dashboard")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Daily Steps", "8,432", "+12% vs yesterday")
    st.line_chart([4000, 7000, 6800, 7500, 8432])
with col2:
    st.metric("Weight Tracking", "68.5 kg", "-0.5 kg this week")
    st.line_chart([69.2, 69.0, 68.9, 68.7, 68.5])
with col3:
    st.metric("Blood Pressure", "120/80", "Normal range")
    st.line_chart([130, 120, 110, 125, 120])

st.markdown("---")

# Appointment calendar
st.subheader("📅 Appointment Calendar")
st.date_input("Select Appointment Date", value=datetime(2025, 6, 15), min_value=datetime(2025, 6, 1), max_value=datetime(2025, 6, 30))

# Medication Schedule
st.subheader("📋 Medication Schedule")
delete_index = None

for i, med in enumerate(st.session_state.medications):
    col1, col2, col3, col4 = st.columns([0.05, 0.55, 0.25, 0.15])
    checkbox_key = f"taken_{i}"
    time_key = f"time_{i}"

    if checkbox_key not in st.session_state:
        st.session_state[checkbox_key] = False

    with col1:
        st.checkbox("", value=st.session_state[checkbox_key], key=checkbox_key)
    with col2:
        st.write(med["name"])
    with col3:
        st.time_input("", value=med["time"], label_visibility="collapsed", key=time_key)
    with col4:
        if st.button("🗑️", key=f"delete_{i}"):
            delete_index = i

# Handle deletion after rendering
if delete_index is not None:
    st.session_state.medications.pop(delete_index)
    st.session_state.pop(f"taken_{delete_index}", None)
    st.session_state.pop(f"time_{delete_index}", None)

    # Shift keys
    total = len(st.session_state.medications)
    for j in range(delete_index, total):
        st.session_state[f"taken_{j}"] = st.session_state.pop(f"taken_{j+1}", False)
        st.session_state[f"time_{j}"] = st.session_state.pop(f"time_{j+1}", st.session_state.medications[j]["time"])

    st.rerun()

# Medication Progress Bar
st.subheader("💊 Daily Medication Progress")
total = len(st.session_state.medications)
taken_count = sum(1 for i in range(total) if st.session_state.get(f"taken_{i}", False))
progress = round(taken_count / total, 2) if total > 0 else 0.0
st.progress(progress, f"{int(progress * 100)}% medications taken today")

# Add Medication Section
with st.expander("➕ Add New Medication"):
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
