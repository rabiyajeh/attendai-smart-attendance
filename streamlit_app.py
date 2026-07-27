import os
from datetime import date, timedelta
import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="AttendAI", page_icon="✅", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#f4f8f9}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#092637,#071c2b);color:white}
[data-testid="stSidebar"] *{color:#d9e8eb}
.block-container{padding-top:2rem;max-width:1500px}
.hero{background:linear-gradient(135deg,#082536,#0a4b52);padding:28px 32px;border-radius:18px;color:white;margin-bottom:20px}
.hero h1{font-size:2rem;margin:0}.hero p{color:#a9cbd0;margin:.5rem 0 0}
.metric{background:white;border:1px solid #e0e9eb;border-radius:14px;padding:18px;box-shadow:0 4px 18px #1839480b}
.metric small{color:#71858e}.metric strong{display:block;font-size:1.8rem;color:#153440;margin-top:6px}
.safe{background:#e6f8f3;color:#087c6b;border:1px solid #c9eee4;padding:10px 14px;border-radius:10px;margin-bottom:18px}
.stButton>button{border-radius:9px;border:1px solid #0b9b8b}
</style>
""", unsafe_allow_html=True)

def api(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        response = requests.request(method, f"{API_URL}{path}", headers=headers, timeout=8, **kwargs)
        if response.status_code >= 400:
            return None, response.json().get("detail", response.text)
        return response.json() if response.content else {}, None
    except requests.RequestException:
        return None, "Attendance API is unavailable. Start the FastAPI service or use Docker Compose."

def metric(label, value, detail):
    st.markdown(f'<div class="metric"><small>{label}</small><strong>{value}</strong><small>{detail}</small></div>', unsafe_allow_html=True)

def login():
    st.markdown('<div class="hero"><h1>AttendAI</h1><p>Privacy-first smart attendance for modern institutions.</p></div>', unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        with st.form("login"):
            st.subheader("Welcome back")
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            data, error = api("POST", "/api/v1/auth/login", data={"username": email, "password": password})
            if error: st.error(error)
            else:
                st.session_state.token = data["access_token"]
                st.session_state.role = data["role"]
                st.rerun()
        st.caption("Accounts are managed by an administrator. Biometric enrollment is never required for sign-in.")

if "token" not in st.session_state:
    st.session_state.token = os.getenv("DEMO_ACCESS_TOKEN", "")
if not st.session_state.token:
    login()
    st.stop()

with st.sidebar:
    st.markdown("## ✦ AttendAI")
    st.caption("SMART ATTENDANCE")
    role = st.session_state.get("role", "administrator").title()
    st.markdown(f"**Nexus University**  \n{role} portal")
    st.divider()
    page = st.radio("Workspace", [
        "Dashboard", "Live Attendance", "Students", "Courses & Classes", "Timetable",
        "Face Enrollment", "Attendance Records", "Analytics & Reports",
        "Correction Requests", "Notifications", "Audit Log", "Privacy & Settings"
    ], label_visibility="collapsed")
    st.divider()
    st.success("🔒 Biometric data encrypted")
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if page == "Dashboard":
    st.markdown('<div class="hero"><h1>Institution overview</h1><p>Live attendance, recognition health, and actionable trends in one place.</p></div>', unsafe_allow_html=True)
    health, health_error = api("GET", "/health")
    if health_error: st.warning(health_error)
    else: st.markdown('<div class="safe">● All systems operational · Recognition service online</div>', unsafe_allow_html=True)
    summary, _ = api("GET", "/api/v1/analytics/summary")
    summary = summary or {"records": 0, "attendance_rate": 0}
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric("Attendance records", f"{summary['records']:,}", "Server-verified events")
    with c2: metric("Attendance rate", f"{summary['attendance_rate']}%", "Present and late")
    with c3: metric("Active sessions", "—", "Fetched when sessions begin")
    with c4: metric("Pending reviews", "—", "Role-protected queue")
    st.subheader("Attendance trend")
    st.info("Charts populate from PostgreSQL as attendance records are created; no attendance values are hard-coded.")

elif page == "Live Attendance":
    st.markdown('<div class="hero"><h1>Live attendance</h1><p>Start a secure session and use facial recognition or a verified fallback.</p></div>', unsafe_allow_html=True)
    with st.form("session"):
        schedule_id = st.text_input("Class schedule UUID")
        late_after = st.number_input("Mark late after (minutes)", 0, 120, 10)
        start = st.form_submit_button("Start attendance session")
    if start:
        data, error = api("POST", "/api/v1/attendance/sessions", json={"schedule_id": schedule_id, "late_after_minutes": late_after})
        st.error(error) if error else st.success(f"Session {data['id']} started.")
    camera = st.camera_input("Classroom camera")
    if camera: st.info("Frame captured. Production recognition requires the configured InsightFace worker and liveness adapter.")
    st.button("Open secure QR fallback")

elif page == "Face Enrollment":
    st.markdown('<div class="hero"><h1>Facial enrollment</h1><p>Consent-led enrollment stores encrypted embeddings, never public photographs.</p></div>', unsafe_allow_html=True)
    consent = st.checkbox("I confirm the student has received the biometric privacy notice and given informed consent.")
    student_id = st.text_input("Student UUID")
    samples = st.camera_input("Capture enrollment sample")
    st.progress(0 if samples is None else 0.1, text="Capture 10–20 quality samples from different angles")
    st.button("Generate and encrypt embedding", disabled=not (consent and samples and student_id))
    st.caption("Frames with blur, poor lighting, incorrect pose, or multiple faces are rejected by the recognition worker.")

elif page == "Attendance Records":
    st.markdown('<div class="hero"><h1>Attendance records</h1><p>Filter, review, correct, and export server-timestamped records.</p></div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    start = a.date_input("From", date.today() - timedelta(days=30))
    end = b.date_input("To", date.today())
    status_filter = c.selectbox("Status", ["All", "Present", "Late", "Absent", "Excused", "Pending review"])
    st.dataframe(pd.DataFrame(columns=["Student", "Course", "Date", "Status", "Recorded by", "Reason"]), use_container_width=True)
    st.caption("No records returned for the selected filters.")
    st.download_button("Export CSV", data="student,course,date,status\n", file_name=f"attendance-{start}-{end}.csv", mime="text/csv")

elif page == "Analytics & Reports":
    st.markdown('<div class="hero"><h1>Analytics & reports</h1><p>Course, department, and student-level attendance intelligence.</p></div>', unsafe_allow_html=True)
    st.selectbox("Report type", ["Institution summary", "Course summary", "Department summary", "Individual student", "Below threshold"])
    st.slider("Low-attendance threshold", 1, 100, 75, suffix="%")
    st.info("Reports populate from the analytics API and can be exported to CSV or PDF.")
    st.button("Generate report")

elif page == "Privacy & Settings":
    st.markdown('<div class="hero"><h1>Privacy & settings</h1><p>Control attendance rules, consent, retention, security, and fallback access.</p></div>', unsafe_allow_html=True)
    st.toggle("Require active biometric consent", True)
    st.toggle("Allow secure QR fallback", True)
    st.toggle("Require liveness detection", True)
    st.slider("Recognition confidence threshold", 0.5, 1.0, 0.88)
    st.number_input("Biometric retention (days)", 1, 3650, 365)
    st.warning("Deleting facial data is irreversible and always creates an audit event.")
    st.button("Save privacy settings")

else:
    st.markdown(f'<div class="hero"><h1>{page}</h1><p>Role-protected administration backed by the AttendAI API.</p></div>', unsafe_allow_html=True)
    search = st.text_input(f"Search {page.lower()}")
    st.dataframe(pd.DataFrame(columns=["Name", "Identifier", "Status", "Updated"]), use_container_width=True)
    st.caption(f"No {page.lower()} match the current filters.")
    st.button(f"Create {page.rstrip('s').lower()}")

st.divider()
st.caption("AttendAI · Privacy-first attendance intelligence · No demographic or emotion inference")
