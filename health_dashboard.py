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
from datetime import datetime

def parse_time_string(tstr):
    try:
        return datetime.strptime(tstr, "%I:%M %p").time()
    except Exception:
        return datetime.strptime(tstr, "%H:%M").time()  # fallback for 24h format
    
def append_medication(name, medication, medication_time):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    if 'medications' not in data:
        data['medications'] = []
    if 'medication_times' not in data:
        data['medication_times'] = []
    if medication:
        # Convert time object to string if needed
        if isinstance(medication_time, time):
            med_time_str = medication_time.strftime("%H:%M")
        else:
            med_time_str = str(medication_time)
        data['medications'].append(medication)
        data['medication_times'].append(med_time_str)
    with open(f'users/{name}.json', 'w') as f:
        json.dump(data, f, indent=0)

st.cache_data.clear()
st.cache_resource.clear()

st.set_page_config(page_title="Aletheia", layout="wide", initial_sidebar_state="expanded")

# --- Modern CSS with Gradients and Glassmorphism ---
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Root Variables */
:root {
    --primary-pink: #e91e63;
    --primary-pink-light: #f8bbd9;
    --primary-pink-gradient: linear-gradient(135deg, #ff6b9d 0%, #e91e63 50%, #f06292 100%);
    --secondary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --tertiary-gradient: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
    --success-gradient: linear-gradient(135deg, #56ccf2 0%, #2f80ed 100%);
    --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    --danger-gradient: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
    --background-gradient: linear-gradient(135deg, #ffeef3 0%, #ffe0e6 25%, #ffd6e0 50%, #ffccd5 75%, #ffc2cc 100%);
    --card-gradient: linear-gradient(135deg, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0.1) 100%);
    --card-shadow: 0 15px 35px rgba(233, 30, 99, 0.15);
    --card-hover-shadow: 0 25px 50px rgba(233, 30, 99, 0.25);
    --glass-bg: rgba(255, 255, 255, 0.3);
    --glass-border: rgba(255, 255, 255, 0.25);
    --medication-shadow: 0 8px 25px rgba(255, 107, 157, 0.2);
}

/* Global Styles */
html, body, .main {
    background: var(--background-gradient);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: #2d3748;
    line-height: 1.6;
}

.block-container {
    padding: 2rem;
    max-width: 1400px;
}

/* Header Styling */
h1, h2, h3, h4, h5, h6 {
    background: var(--primary-pink-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 600;
    margin-bottom: 1rem;
}

/* Main Title */
.main h1 {
    font-size: 2.5rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
}

.main h1::after {
    content: '';
    position: absolute;
    bottom: -10px;
    left: 50%;
    transform: translateX(-50%);
    width: 80px;
    height: 4px;
    background: var(--primary-pink-gradient);
    border-radius: 2px;
}

/* Card Styling */
.stMetric {
    background: var(--card-gradient) !important;
    backdrop-filter: blur(25px);
    border: 1px solid var(--glass-border);
    border-radius: 25px !important;
    padding: 2rem !important;
    box-shadow: var(--card-shadow);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    margin-bottom: 2rem !important;
}

.stMetric::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--primary-pink-gradient);
    border-radius: 25px 25px 0 0;
}

.stMetric::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.stMetric:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: var(--card-hover-shadow);
}

.stMetric:hover::after {
    opacity: 1;
}

/* Metric Values */
.stMetric [data-testid="metric-value"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: var(--primary-pink-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.stMetric [data-testid="metric-delta"] {
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    opacity: 0.8;
}

/* Button Styling */
.stButton > button {
    background: var(--primary-pink-gradient) !important;
    border: none !important;
    border-radius: 30px !important;
    padding: 15px 35px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 8px 25px rgba(233, 30, 99, 0.4) !important;
    position: relative;
    overflow: hidden;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    transition: left 0.6s;
}

.stButton > button::after {
    content: '';
    position: absolute;
    inset: 2px;
    background: var(--tertiary-gradient);
    border-radius: 28px;
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: -1;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.05) !important;
    box-shadow: 0 15px 40px rgba(233, 30, 99, 0.6) !important;
}

.stButton > button:hover::before {
    left: 100%;
}

.stButton > button:hover::after {
    opacity: 1;
}

/* Input Field Styling */
.stTextInput > div > div > input,
.stDateInput input,
.stTextArea textarea,
.stSelectbox > div > div > select {
    border-radius: 20px !important;
    border: 2px solid var(--glass-border) !important;
    background: var(--card-gradient) !important;
    backdrop-filter: blur(15px);
    padding: 15px 20px !important;
    font-size: 1rem !important;
    transition: all 0.4s ease !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08) !important;
}

.stTextInput > div > div > input:focus,
.stDateInput input:focus,
.stTextArea textarea:focus,
.stSelectbox > div > div > select:focus {
    border-color: var(--primary-pink) !important;
    box-shadow: 0 0 0 4px rgba(233, 30, 99, 0.15), 0 10px 30px rgba(0, 0, 0, 0.1) !important;
    outline: none !important;
    background: rgba(255, 255, 255, 0.6) !important;
}

/* Hide time input text box - only dropdown */
.stTimeInput input[type="time"] {
    display: none !important;
}

.stTimeInput select {
    border-radius: 20px !important;
    border: 2px solid var(--glass-border) !important;
    background: var(--card-gradient) !important;
    backdrop-filter: blur(15px);
    padding: 15px 20px !important;
    font-size: 1rem !important;
    transition: all 0.4s ease !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08) !important;
    cursor: pointer;
}

.stTimeInput select:focus {
    border-color: var(--primary-pink) !important;
    box-shadow: 0 0 0 4px rgba(233, 30, 99, 0.15) !important;
    outline: none !important;
}

/* Progress Bar Styling - Fixed for Medication */
.stProgress > div {
    border-radius: 25px !important;
    background: var(--card-gradient) !important;
    backdrop-filter: blur(15px) !important;
    border: 1px solid var(--glass-border) !important;
    overflow: hidden;
    height: 16px !important;
    box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.stProgress > div > div {
    border-radius: 25px !important;
    background: var(--success-gradient) !important;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative;
    overflow: hidden;
}

.stProgress > div > div::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { left: -100%; }
    100% { left: 100%; }
}

.stProgress span {
    background: var(--card-gradient) !important;
    backdrop-filter: blur(10px) !important;
    color: var(--primary-pink) !important;
    padding: 6px 12px !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
    border: 1px solid var(--glass-border) !important;
}

/* Sidebar Styling */
.css-1d391kg {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--glass-border) !important;
}

/* Checkbox Styling */
.stCheckbox input[type="checkbox"] {
    appearance: none;
    width: 20px !important;
    height: 20px !important;
    border: 2px solid var(--primary-pink-light) !important;
    border-radius: 6px !important;
    background: white !important;
    position: relative;
    cursor: pointer;
    transition: all 0.3s ease !important;
}

.stCheckbox input[type="checkbox"]:checked {
    background: var(--primary-pink-gradient) !important;
    border-color: var(--primary-pink) !important;
}

.stCheckbox input[type="checkbox"]:checked::after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    font-weight: bold;
    font-size: 12px;
}

/* File Uploader Styling */
.stFileUploader > div {
    border: 2px dashed var(--primary-pink-light) !important;
    border-radius: 15px !important;
    background: rgba(255, 255, 255, 0.5) !important;
    backdrop-filter: blur(10px);
    padding: 2rem !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
}

.stFileUploader > div:hover {
    border-color: var(--primary-pink) !important;
    background: rgba(255, 255, 255, 0.7) !important;
}

/* Expander Styling */
.streamlit-expanderHeader {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border-radius: 15px !important;
    border: 1px solid var(--glass-border) !important;
    padding: 1rem !important;
    font-weight: 600 !important;
    color: var(--primary-pink) !important;
}

.streamlit-expanderContent {
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(10px);
    border-radius: 0 0 15px 15px !important;
    border: 1px solid var(--glass-border) !important;
    border-top: none !important;
    padding: 1rem !important;
}

/* Chart Styling */
.stPlotlyChart {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border-radius: 15px !important;
    border: 1px solid var(--glass-border) !important;
    padding: 1rem !important;
    box-shadow: var(--card-shadow) !important;
}

/* Alert/Info Box Styling */
.stInfo {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border-left: 4px solid var(--primary-pink) !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

.stSuccess {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border-left: 4px solid #4caf50 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

.stWarning {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border-left: 4px solid #ff9800 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

.stError {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border-left: 4px solid #f44336 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

/* Custom Insurance Container */
.insurance-container {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    border: 1px solid var(--glass-border);
    padding: 2rem;
    margin: 1rem 0;
    box-shadow: var(--card-shadow);
}

.insurance-score {
    font-size: 2.5rem;
    font-weight: 700;
    background: var(--primary-pink-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    padding: 1rem 0;
}

/* Medication Schedule Styling */
.medication-item {
    background: var(--card-gradient);
    backdrop-filter: blur(25px);
    border-radius: 20px;
    border: 1px solid var(--glass-border);
    padding: 1.5rem;
    margin: 1.5rem 0;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--medication-shadow);
    position: relative;
    overflow: hidden;
}

.medication-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--tertiary-gradient);
    border-radius: 20px 20px 0 0;
}

.medication-item:hover {
    transform: translateX(8px) translateY(-2px);
    box-shadow: 0 15px 40px rgba(255, 107, 157, 0.3);
    border-color: var(--primary-pink-light);
}

.medication-item:hover::before {
    background: var(--primary-pink-gradient);
}

/* Medication spacing improvements */
.medication-container {
    padding: 2rem 0;
}

.medication-container .stColumns {
    margin-bottom: 1rem !important;
}

/* Enhanced medication buttons */
.medication-item .stButton > button {
    padding: 8px 16px !important;
    font-size: 0.9rem !important;
    border-radius: 20px !important;
    margin: 0 5px !important;
}

.medication-explain-btn {
    background: var(--warning-gradient) !important;
}

.medication-delete-btn {
    background: var(--danger-gradient) !important;
}

/* Hero Section */
.hero-section {
    background: var(--card-gradient);
    backdrop-filter: blur(30px);
    border-radius: 30px;
    border: 1px solid var(--glass-border);
    padding: 4rem 3rem;
    margin: 3rem 0;
    text-align: center;
    box-shadow: var(--card-shadow);
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 182, 193, 0.1) 0%, transparent 70%);
    animation: float 6s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translate(0, 0) rotate(0deg); }
    50% { transform: translate(-20px, -10px) rotate(1deg); }
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 800;
    background: var(--primary-pink-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 1.5rem;
    text-shadow: 0 4px 8px rgba(233, 30, 99, 0.2);
    position: relative;
    z-index: 1;
}

.hero-subtitle {
    font-size: 1.4rem;
    color: #6b7280;
    margin-bottom: 2.5rem;
    font-weight: 500;
    position: relative;
    z-index: 1;
}

/* Divider Styling - No hover effects */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--primary-pink-light), transparent) !important;
    margin: 2rem 0 !important;
    transform: none !important;
    transition: none !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem !important;
    }
    
    .hero-title {
        font-size: 2rem !important;
    }
    
    .hero-subtitle {
        font-size: 1rem !important;
    }
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: var(--primary-pink-gradient);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary-pink);
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

# --- Sidebar (Only on Dashboard) ---
if "profile" not in st.session_state:
    st.session_state.profile = {}

if st.session_state.tab == "dashboard":
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <h2 style="margin-bottom: 0.5rem;">👤 Profile Setup</h2>
            <p style="color: #6b7280; font-size: 0.9rem;">Complete your health profile</p>
        </div>
        """, unsafe_allow_html=True)
        
        full_name = st.text_input("👤 Full Name", placeholder="Enter your full name")
        if full_name:
            st.session_state.first_name = full_name.split()[0] if full_name.strip() else "profile"
        contact = st.text_input("📞 Contact Number", placeholder="+1 (555) 123-4567")
        email = st.text_input("📧 Email Address", placeholder="your.email@example.com")
        consultant = st.text_input("👩‍⚕️ Healthcare Consultant", value="Dr. Sarah Johnson", disabled=True)
        
        st.markdown("---")
        
        document_upload = st.file_uploader("📎📄 Upload Medical Documents", type=["pdf", "jpg", "jpeg", "png"], key="med_doc")

        st.session_state.profile.update({
            "full_name": full_name,
            "contact": contact,
            "email": email,
            "consultant": consultant
        })

        if st.button("Submit Profile"):
            if document_upload:
                with st.spinner("🔍 Analyzing document..."):
                    response = doc_parser.doc_parser(document_upload, f'{full_name.split()[0]}.json')
                    if response:
                        try:
                            data = json.loads(response) if isinstance(response, str) else response
                            print(data)
                            st.session_state.uploaded_medical_history = data.get("medical_history", {})
                            st.session_state.uploaded_doctors_note = data.get("doctor's note", "")
                            st.session_state.uploaded_bmi = data.get("bmi", "")
                            st.session_state.uploaded_height = data.get("height", "")
                            st.session_state.uploaded_bp = data.get("bp", "")
                            st.session_state.first_name = full_name.split()[0] if full_name.strip() else "profile"
                            append_doctor_notes(st.session_state.first_name, st.session_state.uploaded_doctors_note)
                            write_medical_history(st.session_state.first_name, st.session_state.uploaded_medical_history)
                            append_user_stats(st.session_state.first_name, st.session_state.uploaded_bmi, st.session_state.uploaded_height, st.session_state.uploaded_bp)
                            # Add all medicines and medicine_times to user JSON
                            medicines = data.get("medications", [])
                            medicine_times = data.get("medication_times", [])
                            print(medicines)
                            print(medicine_times)
                            for med, med_time_str in zip(medicines, medicine_times):
                                try:
                                    med_time = parse_time_string(med_time_str)
                                except Exception:
                                    med_time = time(9, 0)
                                print(med, med_time)
                                append_medication(st.session_state.first_name, med, med_time)
                            st.success(f"✅ Document processed successfully!\n{data["summary"]}")
                        except Exception as e:
                            st.error(f"❌ Failed to parse document: {e}")
                    else:
                        st.warning("⚠️ No response from document parser.")

# Medication Logic
if not st.session_state.get("medications"):
    st.session_state.medications = []
    try:
        with open(f'users/{st.session_state.first_name}.json', 'r') as f:
            data = json.load(f)
        meds = data.get("medications", [])
        med_times = data.get("medication_times", [])
        for i, med in enumerate(meds):
            med_time_str = med_times[i] if i < len(med_times) else "09:00"
            st.session_state.medications.append({
                'name': med,
                'time': parse_time_string(med_time_str)
            })
    except Exception as e:
        st.warning(f"Could not load medications: {e}")

# --- Dashboard Tab ---
if st.session_state.tab == "dashboard":
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🌸 Welcome To Aletheia!</div>
        <div class="hero-subtitle">Your comprehensive health and wellness companion</div>
    </div>
    """, unsafe_allow_html=True)

    # Health Metrics - Changed from Steps to BMI
    st.markdown("### 📊 Health Overview")
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

    st.markdown("---")

    # Calendar and Progress Section
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 📅 Appointment Calendar")
        st.date_input(
            "Select Appointment Date", 
            value=datetime(2025, 6, 15),
            min_value=datetime(2025, 6, 1), 
            max_value=datetime(2025, 6, 30)
        )
        
    with col_right:
        st.markdown("### 📈 Daily Medication Progress")
        total = len(st.session_state.medications)
        taken = sum([1 for i in range(total) if st.session_state.get(f"taken_{i}", False)])
        percent = taken / total if total > 0 else 0.0
        st.progress(percent, f"{round(percent * 100)}% completed today")

    st.markdown("---")

    # Medication Schedule
    st.markdown("### 💊 Medication Schedule")
    
    # Create medication container with better spacing
    st.markdown('<div class="medication-container">', unsafe_allow_html=True)
    
    delete_index = None
    for i, med in enumerate(st.session_state.medications):
        # Create medication item container with enhanced styling
        st.markdown(f"""
        <div class="medication-item">
        """, unsafe_allow_html=True)
        
        cols = st.columns([0.1, 0.4, 0.25, 0.1, 0.1, 0.05])
        checkbox_key = f"taken_{i}"
        time_key = f"time_{i}"
        
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False
            
        with cols[0]:
            st.checkbox("", value=st.session_state[checkbox_key], key=checkbox_key, help="Mark as taken")
            
        with cols[1]:
            status_emoji = "✅" if st.session_state[checkbox_key] else "⏰"
            status_text = "Completed" if st.session_state[checkbox_key] else "Pending"
            st.markdown(f"""
            <div style="padding: 0.5rem 0;">
                <div style="font-size: 1.1rem; font-weight: 600; color: #2d3748;">
                    {status_emoji} {med['name']}
                </div>
                <div style="font-size: 0.9rem; color: #6b7280; margin-top: 0.25rem;">
                    Status: {status_text}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with cols[2]:
            # Create time dropdown options
            time_options = []
            for hour in range(24):
                for minute in [0, 30]:
                    time_str = f"{hour:02d}:{minute:02d}"
                    time_options.append(time_str)
            
            current_time_str = med["time"].strftime("%H:%M")
            selected_time = st.selectbox(
                "", 
                time_options,
                index=time_options.index(current_time_str) if current_time_str in time_options else 0,
                key=time_key,
                label_visibility="collapsed"
            )
            
            # Update medication time when changed
            if selected_time:
                hour, minute = map(int, selected_time.split(':'))
                med["time"] = time(hour, minute)
            
        with cols[3]:
            if st.button("💡", key=f"explain_{i}", help="Get explanation"):
                st.session_state[f"show_explain_{i}"] = not st.session_state.get(f"show_explain_{i}", False)
                
        with cols[4]:
            if st.button("🗑️", key=f"delete_{i}", help="Delete medication"):
                delete_index = i
                st.session_state.medications.pop(delete_index)
                st.rerun()

        # Show explanation if toggled - Only call AI when button is pressed
        if st.session_state.get(f"show_explain_{i}", False):
            st.markdown("---")
            with st.container():
                st.markdown("**📋 Medication Information**")
                # Only generate explanation if not already cached
                explanation_key = f"explanation_{i}_{med['name']}"
                if explanation_key not in st.session_state:
                    raw_response = medicine_explainer.medicine_explainer(med["name"])
                    
                    # Debug: Show what we received
                    # st.write(f"Debug - Raw response type: {type(raw_response)}")
                    # st.write(f"Debug - Raw response: {str(raw_response)[:200]}...")
                    
                    # Parse JSON response and extract only the "response" field
                    cleaned_response = raw_response
                    try:
                        # Handle string responses that might be JSON
                        if isinstance(raw_response, str):
                            # Try to parse as JSON
                            if raw_response.strip().startswith('{') and raw_response.strip().endswith('}'):
                                parsed_response = json.loads(raw_response)
                                cleaned_response = parsed_response.get("response", raw_response)
                            else:
                                # Not JSON, use as is
                                cleaned_response = raw_response
                        # Handle dict responses
                        elif isinstance(raw_response, dict):
                            cleaned_response = raw_response.get("response", str(raw_response))
                        else:
                            # Other types, convert to string
                            cleaned_response = str(raw_response)
                            
                        st.session_state[explanation_key] = cleaned_response
                        
                    except (json.JSONDecodeError, AttributeError) as e:
                        # If parsing fails, use the raw response but try to clean it
                        if isinstance(raw_response, str) and '"response":' in raw_response:
                            # Try to extract response manually if JSON parsing failed
                            try:
                                start = raw_response.find('"response":"') + 12
                                end = raw_response.find('","', start)
                                if end == -1:
                                    end = raw_response.find('"}', start)
                                if start > 11 and end > start:
                                    cleaned_response = raw_response[start:end].replace('\\"', '"')
                                else:
                                    cleaned_response = raw_response
                            except:
                                cleaned_response = raw_response
                        else:
                            cleaned_response = raw_response
                        st.session_state[explanation_key] = cleaned_response
                
                # Display the cleaned response
                st.info(st.session_state[explanation_key])
                
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

    # Sync times after all UI
    for i, med in enumerate(st.session_state.medications):
        time_key = f"time_{i}"
        if time_key in st.session_state:
            selected_time = st.session_state[time_key]
            if selected_time:
                hour, minute = map(int, selected_time.split(':'))
                med["time"] = time(hour, minute)
    
    # Check for missed medications
    st.session_state.missed_medications = []
    st.session_state.current_time = datetime.now()
    for medication in st.session_state.medications:
        if medication["time"] < st.session_state.current_time.time():
            st.session_state.missed_medications.append({"name": medication["name"]})

    # Show missed medications
    if len(st.session_state.missed_medications) != 0:
        with st.expander("⚠️ Missed Medications", expanded=False):
            for i, med in enumerate(st.session_state.missed_medications):
                st.warning(f"**{med['name']}** - Scheduled earlier today")
                user_question = st.text_input(f"Ask about missed: {med['name']}", key=f"missed_q_{i}", placeholder="What should I do?")
                if st.button(f"🤖 Get Advice: {med['name']}", key=f"missed_{i}"):
                    # Cache AI response to prevent repeated calls
                    advice_key = f"advice_{i}_{med['name']}_{user_question}"
                    if advice_key not in st.session_state:
                        if user_question.strip():
                            raw_advice = conversation.conversation(f"I missed my {med['name']}. {user_question}")
                        else:
                            raw_advice = conversation.conversation(f"I missed my {med['name']}. What should I do?")
                        
                        # Parse JSON response and extract only the "response" field
                        cleaned_advice = raw_advice
                        try:
                            # Handle string responses that might be JSON
                            if isinstance(raw_advice, str):
                                # Try to parse as JSON
                                if raw_advice.strip().startswith('{') and raw_advice.strip().endswith('}'):
                                    parsed_advice = json.loads(raw_advice)
                                    cleaned_advice = parsed_advice.get("response", raw_advice)
                                else:
                                    # Not JSON, use as is
                                    cleaned_advice = raw_advice
                            # Handle dict responses
                            elif isinstance(raw_advice, dict):
                                cleaned_advice = raw_advice.get("response", str(raw_advice))
                            else:
                                # Other types, convert to string
                                cleaned_advice = str(raw_advice)
                                
                            st.session_state[advice_key] = cleaned_advice
                            
                        except (json.JSONDecodeError, AttributeError) as e:
                            # If parsing fails, try manual extraction
                            if isinstance(raw_advice, str) and '"response":' in raw_advice:
                                try:
                                    start = raw_advice.find('"response":"') + 12
                                    end = raw_advice.find('","', start)
                                    if end == -1:
                                        end = raw_advice.find('"}', start)
                                    if start > 11 and end > start:
                                        cleaned_advice = raw_advice[start:end].replace('\\"', '"')
                                    else:
                                        cleaned_advice = raw_advice
                                except:
                                    cleaned_advice = raw_advice
                            else:
                                cleaned_advice = raw_advice
                            st.session_state[advice_key] = cleaned_advice
                    
                    st.info(st.session_state[advice_key])

    # Add new medication
    if "new_med_name" not in st.session_state:
        st.session_state.new_med_name = ""
    if "new_med_time" not in st.session_state:
        st.session_state.new_med_time = time(9, 0)  # Default to 09:00
    with st.expander("➕ Add New Medication", expanded=False):
        st.markdown("### Add Medication to Schedule")
        
        col_med1, col_med2 = st.columns(2)
        with col_med1:
            st.session_state.new_med_name = st.text_input(
                "💊 Medication Name", 
                st.session_state.new_med_name, 
                key="add_name", 
                placeholder="Enter medication name"
            )
        
        with col_med2:
            # Create time dropdown for adding medication
            time_options = []
            for hour in range(24):
                for minute in [0, 30]:
                    time_str = f"{hour:02d}:{minute:02d}"
                    time_options.append(time_str)
            
            current_time_str = st.session_state.new_med_time.strftime("%H:%M")
            selected_new_time = st.selectbox(
                "⏰ Schedule Time",
                time_options,
                index=time_options.index(current_time_str) if current_time_str in time_options else 18,  # Default to 9:00 AM
                key="add_time_select"
            )
            
            if selected_new_time:
                hour, minute = map(int, selected_new_time.split(':'))
                st.session_state.new_med_time = time(hour, minute)
        
        if st.button("➕ Add Medication", use_container_width=True):
            name = st.session_state.new_med_name.strip()
            if name:
                st.session_state.medications.append({
                    "name": name,
                    "time": st.session_state.new_med_time,
                })
                st.session_state[f"taken_{len(st.session_state.medications) - 1}"] = False
                st.session_state.new_med_name = ""
                # --- Add to JSON file ---
                append_medication_to_json(st.session_state.first_name, name, st.session_state.new_med_time)
                st.success("✅ Medication added successfully!")
                st.rerun()

    st.markdown("---")

    # Medical History Section
    st.markdown("### 📋 Medical History & Doctor Notes")

    if st.session_state.profile.get("full_name"):
        user_file = f"users/{st.session_state.profile['full_name']}.json"

        if not os.path.exists("users"):
            os.makedirs("users")
        if not os.path.exists(user_file):
            with open(user_file, 'w') as f:
                json.dump({"medical_history": [], "doctor_notes": []}, f, indent=4)

    col_hist, col_notes = st.columns(2)
    
    with col_hist:
        st.markdown("""
        <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 20px; 
                    border: 1px solid var(--glass-border); padding: 1.5rem; box-shadow: var(--card-shadow);">
            <h4 style="margin-bottom: 1rem;">📚 Latest Medical History</h4>
        """, unsafe_allow_html=True)
        
        med_hist = read_medical_history(st.session_state.get('first_name', st.session_state.profile.get('full_name', 'profile')))
        if med_hist and len(med_hist) > 0:
            latest_entry = med_hist[-1]
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.7); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid var(--primary-pink);">
                <strong>Latest Entry:</strong><br>
                {latest_entry}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No medical history entries yet.")

        new_entry = st.text_input("Add Medical History Entry", placeholder="Enter condition, allergy, etc.")
        if st.button("➕ Add History", key="add_history"):
            if new_entry.strip():
                write_medical_history(st.session_state.profile["full_name"], new_entry)
                st.success("✅ Added to medical history.")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

        with col_notes:
            st.markdown("""
            <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 20px; 
                        border: 1px solid var(--glass-border); padding: 1.5rem; box-shadow: var(--card-shadow);">
                <h4 style="margin-bottom: 1rem;">👩‍⚕️ Doctor's Notes</h4>
            """, unsafe_allow_html=True)
            
            doc_notes = read_doctor_notes(st.session_state.get('first_name', st.session_state.profile.get('full_name', 'profile')))
            if doc_notes and len(doc_notes) > 0:
                latest_note = doc_notes[-1]
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.7); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid var(--primary-pink);">
                    <strong>Latest Note:</strong><br>
                    {latest_note}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No doctor notes recorded.")

            new_note = st.text_input("Add Doctor Note", placeholder="Enter doctor's recommendation")
            if st.button("➕ Add Note", key="add_note"):
                if new_note.strip():
                    append_doctor_notes(st.session_state.profile["full_name"], new_note)
                    st.success("✅ Doctor note added.")
                    st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigation Buttons with enhanced styling
    st.markdown("""
    <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 25px; 
                border: 1px solid var(--glass-border); padding: 2rem; box-shadow: var(--card-shadow); 
                margin: 2rem 0;">
        <h4 style="text-align: center; margin-bottom: 2rem;">🚀 Explore More Features</h4>
    """, unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🛡️ Insurance Review", use_container_width=True):
            st.session_state.tab = "insurance"
            st.rerun()
    with col_btn2:
        if st.button("📷 Scan Medication", use_container_width=True):
            st.session_state.tab = "scan"
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

# --- Insurance Tab ---
elif st.session_state.tab == "insurance":
    st.markdown('<div class="insurance-container">', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">🛡️ Insurance Review</h1>
        <p style="font-size: 1.2rem; color: #6b7280;">Analyze and compare insurance providers with AI insights</p>
    </div>
    """, unsafe_allow_html=True)

    provider = st.text_input("🏢 Insurance Provider Name", placeholder="Enter insurance company name")
    run_analysis = st.button("🔍 Analyze Provider", use_container_width=True)
    insurance_data = None

    if run_analysis and provider.strip():
        # Clear any previous analysis data to prevent cache issues
        if "insurance_analysis_cache" in st.session_state:
            del st.session_state["insurance_analysis_cache"]
        
        with st.spinner("🔍 Running comprehensive insurance analysis..."):
            # Create unique context for this specific provider
            context = (
                f"User is requesting analysis for {provider} insurance company. "
                "User is a 32-year-old freelance graphic designer living in Los Angeles, earning "
                "≈ $85k/year pre-tax with irregular cash-flow, mild asthma, type-2 diabetes family "
                "history, newly married and planning children in ≤ 3 yrs. Needs PPO that covers "
                "Cedars-Sinai + UCLA, strong maternity, fears high deductibles after a $4k ER bill, "
                "values ESG & companies with clean denial records, wants first-class mobile app, "
                "travels abroad ~6×/yr. Please analyze specifically {provider} and provide alternatives."
            )
            try:
                # Force fresh analysis by passing clear provider name
                insurance_data = analyze_insurance(provider.strip(), context)
                
                # Save analysis with timestamp and provider name for debugging
                analysis_filename = f"backend/insurance_analysis_{provider.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(analysis_filename, "w", encoding="utf-8") as f:
                    json.dump({
                        "provider": provider,
                        "timestamp": datetime.now().isoformat(),
                        "analysis": insurance_data
                    }, f, ensure_ascii=False, indent=4)
                    
                # Also save to the main output file
                with open("backend/insurance_analysis_output.json", "w", encoding="utf-8") as f:
                    json.dump({
                        "provider": provider,
                        "timestamp": datetime.now().isoformat(),
                        "analysis": insurance_data
                    }, f, ensure_ascii=False, indent=4)
                    
                st.success(f"✅ Analysis complete for {provider}!")
                
            except Exception as e:
                st.error(f"❌ Failed to analyze {provider}: {e}")
                insurance_data = None

    if insurance_data:
        # Verify we're showing the correct provider analysis
        st.markdown(f"""
        <div style="background: var(--warning-gradient); border-radius: 15px; padding: 1rem; margin: 1rem 0; text-align: center;">
            <strong>📊 Analysis Results for: {provider}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # Trust Index Display with enhanced styling
        st.markdown("""
        <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 25px; 
                    border: 1px solid var(--glass-border); padding: 2rem; box-shadow: var(--card-shadow); 
                    margin: 2rem 0; text-align: center;">
            <h3>📈 Overall Trust Index</h3>
        """, unsafe_allow_html=True)
        
        trust = insurance_data.get("trust_index", 0)
        
        col_trust1, col_trust2, col_trust3 = st.columns([1, 2, 1])
        with col_trust2:
            st.markdown(f"""
            <div style="font-size: 3rem; font-weight: 800; 
                        background: var(--primary-pink-gradient); 
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                        text-align: center; margin: 1rem 0;">
                {trust} / 10
            </div>
            <p style="text-align: center; font-size: 1.2rem; color: #6b7280; margin-bottom: 1rem;">
                {provider}
            </p>
            """, unsafe_allow_html=True)
            st.progress(int(trust * 10), f"Trust Score: {trust}/10")
            
        st.markdown("</div>", unsafe_allow_html=True)

        # Alternatives with enhanced styling
        st.markdown("""
        <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 25px; 
                    border: 1px solid var(--glass-border); padding: 2rem; box-shadow: var(--card-shadow); 
                    margin: 2rem 0;">
            <h3 style="text-align: center; margin-bottom: 2rem;">🏆 Alternative Providers</h3>
        """, unsafe_allow_html=True)
        
        alts = insurance_data.get("alternatives", [])
        
        if alts:
            col1, col2 = st.columns(2)
            left = alts[: len(alts)//2 + len(alts)%2]
            right = alts[len(left):]

            def render_alt(column, items):
                with column:
                    for alt in items:
                        name = alt.get("name", "—")
                        score = alt.get("trust_index", 0)
                        st.markdown(f"""
                        <div style="background: rgba(255, 255, 255, 0.1); border-radius: 15px; 
                                    padding: 1rem; margin: 0.5rem 0; border: 1px solid var(--glass-border);">
                            <h5 style="margin-bottom: 0.5rem;">{name}</h5>
                        </div>
                        """, unsafe_allow_html=True)
                        st.progress(int(score * 10), f"{score}/10")

            render_alt(col1, left)
            render_alt(col2, right)
        else:
            st.info("No alternative providers found.")
            
        st.markdown("</div>", unsafe_allow_html=True)

        # Reviews with enhanced styling
        st.markdown("""
        <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 25px; 
                    border: 1px solid var(--glass-border); padding: 2rem; box-shadow: var(--card-shadow); 
                    margin: 2rem 0;">
            <h3>💬 Recent Customer Reviews</h3>
        """, unsafe_allow_html=True)
        
        reviews = insurance_data.get("reviews", [])
        if reviews:
            for i, r in enumerate(reviews):
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.1); border-radius: 15px; 
                            padding: 1rem; margin: 1rem 0; border-left: 4px solid var(--primary-pink);">
                    💭 {r}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No recent reviews found.")
            
        st.markdown("</div>", unsafe_allow_html=True)

        # Company Background with enhanced styling
        st.markdown("""
        <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 25px; 
                    border: 1px solid var(--glass-border); padding: 2rem; box-shadow: var(--card-shadow); 
                    margin: 2rem 0;">
            <h3>📝 Company Background & Analysis</h3>
        """, unsafe_allow_html=True)
        
        # Show provider name again to confirm correct analysis
        st.markdown(f"**Analyzing: {provider}**")
        
        desc = insurance_data.get("description", "")
        if isinstance(desc, list):
            desc = "\n".join(desc)
        if desc:
            st.markdown(desc)
        else:
            st.info(f"No detailed company information available for {provider}.")
            
        st.markdown("</div>", unsafe_allow_html=True)

        # Supporting Links with enhanced styling
        st.markdown("""
        <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 25px; 
                    border: 1px solid var(--glass-border); padding: 2rem; box-shadow: var(--card-shadow); 
                    margin: 2rem 0;">
            <h3>🔗 Supporting Resources</h3>
        """, unsafe_allow_html=True)
        
        links = insurance_data.get("links", [])
        if links:
            for link in links:
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.1); border-radius: 10px; 
                            padding: 0.5rem 1rem; margin: 0.5rem 0;">
                    🌐 <a href="{link}" target="_blank" style="color: var(--primary-pink); text-decoration: none;">{link}</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No additional resources found.")
            
        st.markdown("</div>", unsafe_allow_html=True)
            
    elif run_analysis:
        st.error(f"❌ Insurance analysis returned no usable data for {provider}.")
        
    # Debug section (can be uncommented for troubleshooting)
    # if st.checkbox("🔧 Show Debug Info"):
    #     st.write(f"Current provider input: '{provider}'")
    #     st.write(f"Analysis button clicked: {run_analysis}")
    #     if 'insurance_data' in locals():
    #         st.write(f"Insurance data received: {bool(insurance_data)}")
    #     if insurance_data:
    #         st.write("Raw insurance data:", insurance_data)

    # Back button
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.tab = "dashboard"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- Scan Medication Tab ---
elif st.session_state.tab == "scan":
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">📷 Medication Scanner</h1>
        <p style="font-size: 1.2rem; color: #6b7280;">Upload a photo to identify your medication with AI technology</p>
    </div>
    """, unsafe_allow_html=True)

    # Upload Section with enhanced styling
    st.markdown("""
    <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 25px; 
                border: 1px solid var(--glass-border); padding: 3rem; box-shadow: var(--card-shadow); 
                margin: 2rem 0;">
    """, unsafe_allow_html=True)
    
    col_upload1, col_upload2, col_upload3 = st.columns([1, 2, 1])
    with col_upload2:
        image = st.file_uploader(
            "📸 Upload Medication Image", 
            type=["jpg", "jpeg", "png"],
            help="Take a clear photo of your pill or medication bottle"
        )
        
        if image:
            st.image(image, caption="Uploaded medication image", use_column_width=True)
            
            # Only process when analyze button is clicked
            if st.button("🔍 Analyze Image", use_container_width=True):
                with st.spinner("🔍 Analyzing medication..."):
                    try:
                        raw_response = pill_identifier.pill_identifier(image)
                        
                        # Parse JSON response and extract only the "response" field for medication name
                        medication_name = raw_response
                        try:
                            # Handle string responses that might be JSON
                            if isinstance(raw_response, str):
                                # Try to parse as JSON
                                if raw_response.strip().startswith('{') and raw_response.strip().endswith('}'):
                                    parsed_response = json.loads(raw_response)
                                    medication_name = parsed_response.get("response", raw_response)
                                else:
                                    # Not JSON, use as is
                                    medication_name = raw_response
                            # Handle dict responses
                            elif isinstance(raw_response, dict):
                                medication_name = raw_response.get("response", str(raw_response))
                            else:
                                # Other types, convert to string
                                medication_name = str(raw_response)
                                
                        except (json.JSONDecodeError, AttributeError) as e:
                            # If parsing fails, try manual extraction
                            if isinstance(raw_response, str) and '"response":' in raw_response:
                                try:
                                    start = raw_response.find('"response":"') + 12
                                    end = raw_response.find('","', start)
                                    if end == -1:
                                        end = raw_response.find('"}', start)
                                    if start > 11 and end > start:
                                        medication_name = raw_response[start:end].replace('\\"', '"')
                                    else:
                                        medication_name = raw_response
                                except:
                                    medication_name = raw_response
                            else:
                                medication_name = raw_response
                        
                        st.success("✅ Medication identified!")
                        
                        st.markdown(f"""
                        <div style="background: rgba(255, 255, 255, 0.2); border-radius: 15px; 
                                    padding: 1rem; margin: 1rem 0; border-left: 4px solid var(--success-gradient);">
                            <strong>Identified Medication:</strong> {medication_name}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Get detailed analysis
                        with st.spinner("📋 Getting detailed information..."):
                            raw_analysis = pill_identifier.pill_explainer(medication_name)
                            pricing_info = pill_identifier.find_cheapest_price(medication_name)
                            
                            try:
                                parsed_analysis = json.loads(raw_analysis)
                                analysis = parsed_analysis['summary']
                            except: 
                                analysis = raw_analysis

                            if pricing_info:
                                analysis += f"\n\n** Pricing Information:**\nLink to buy: {pricing_info['link']}\nPrice: ${pricing_info['price']}"

                            # raw_analysis = medicine_explainer.medicine_explainer(medication_name)
                            
                            # # Parse JSON response and extract only the "response" field for analysis
                            # analysis = raw_analysis
                            # try:
                            #     # Handle string responses that might be JSON
                            #     if isinstance(raw_analysis, str):
                            #         # Try to parse as JSON
                            #         if raw_analysis.strip().startswith('{') and raw_analysis.strip().endswith('}'):
                            #             parsed_analysis = json.loads(raw_analysis)
                            #             analysis = parsed_analysis.get("response", raw_analysis)
                            #         else:
                            #             # Not JSON, use as is
                            #             analysis = raw_analysis
                            #     # Handle dict responses
                            #     elif isinstance(raw_analysis, dict):
                            #         analysis = raw_analysis.get("response", str(raw_analysis))
                            #     else:
                            #         # Other types, convert to string
                            #         analysis = str(raw_analysis)
                                    
                            # except (json.JSONDecodeError, AttributeError) as e:
                            #     # If parsing fails, try manual extraction
                            #     if isinstance(raw_analysis, str) and '"response":' in raw_analysis:
                            #         try:
                            #             start = raw_analysis.find('"response":"') + 12
                            #             end = raw_analysis.find('","', start)
                            #             if end == -1:
                            #                 end = raw_analysis.find('"}', start)
                            #             if start > 11 and end > start:
                            #                 analysis = raw_analysis[start:end].replace('\\"', '"')
                            #             else:
                            #                 analysis = raw_analysis
                            #         except:
                            #             analysis = raw_analysis
                            #     else:
                            #         analysis = raw_analysis
                            
                            st.markdown("### 📋 Medication Information")
                            st.markdown(f"""
                            <div style="background: rgba(255, 255, 255, 0.1); border-radius: 15px; 
                                        padding: 1.5rem; margin: 1rem 0;">
                                {analysis}
                            </div>
                            """, unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"❌ Failed to analyze image: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Instructions with enhanced styling
    st.markdown("---")
    st.markdown("""
    <div style="background: var(--card-gradient); backdrop-filter: blur(25px); border-radius: 25px; 
                border: 1px solid var(--glass-border); padding: 2rem; box-shadow: var(--card-shadow); 
                margin: 2rem 0;">
        <h3 style="text-align: center; margin-bottom: 2rem;">📝 How to Use</h3>
    """, unsafe_allow_html=True)
    
    col_inst1, col_inst2, col_inst3 = st.columns(3)
    with col_inst1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📸</div>
            <h4>Step 1: Take Photo</h4>
            <p style="color: #6b7280;">
                • Use good lighting<br>
                • Keep medication in focus<br>
                • Include any text/numbers
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_inst2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
            <h4>Step 2: Upload & Scan</h4>
            <p style="color: #6b7280;">
                • Upload your clear photo<br>
                • Click analyze button<br>
                • Review identification
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_inst3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💊</div>
            <h4>Step 3: Get Info</h4>
            <p style="color: #6b7280;">
                • Read medication details<br>
                • Check dosage information<br>
                • Add to your schedule
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.tab = "dashboard"
        st.rerun()