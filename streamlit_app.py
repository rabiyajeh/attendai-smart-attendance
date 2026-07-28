import io
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from attendai.database import init_db, query, execute, scalar, hash_password, verify_password, audit, utcnow
from attendai.vision import decode_image, detect_and_embed, encrypt_embedding, decrypt_embedding, similarity, annotate, cv_available, CV_IMPORT_ERROR

st.set_page_config(page_title="AttendAI Vision", page_icon="👁️", layout="wide")
init_db()
st.markdown("""<style>
[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#f4f8f9;color:#173541}
[data-testid="stSidebar"]{background:#082332}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] span{color:#dcebed!important}
.block-container{max-width:1500px;padding-top:1.5rem}
.hero{padding:25px 30px;border-radius:18px;color:white;background:linear-gradient(135deg,#082536,#087f77);margin-bottom:18px}
.hero h1{margin:0;color:#fff!important}.hero p{color:#d8f0ef!important;margin:.4rem 0 0}
.metric{background:#fff;border:1px solid #e1e9eb;border-radius:14px;padding:18px}.metric small{color:#70848c}
.metric strong{display:block;font-size:1.8rem;color:#163541}.safe{padding:10px 14px;border-radius:9px;background:#e5f8f2;color:#087967}
[data-testid="stWidgetLabel"] p,.stMarkdown p,.stCaptionContainer p,
[data-testid="stForm"] label p,[data-testid="stExpander"] summary p{color:#314b57!important}
.stMarkdown .hero p{color:#d8f0ef!important}
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div,
[data-baseweb="textarea"]{background:#fff!important;color:#173541!important;border-color:#cbdadd!important}
[data-baseweb="input"] input,[data-baseweb="base-input"] input,[data-baseweb="textarea"] textarea{
background:#fff!important;color:#173541!important;-webkit-text-fill-color:#173541!important}
[data-baseweb="input"] svg,[data-baseweb="select"] svg{color:#536b75!important;fill:#536b75!important}
[data-testid="stForm"]{background:#fff;border-color:#d8e5e7}
[data-testid="stAlert"] p{color:inherit!important}
.stButton>button,.stFormSubmitButton>button{background:#078c80;color:#fff;border:1px solid #06766d;font-weight:700}
.stButton>button:hover,.stFormSubmitButton>button:hover{background:#066f67;color:#fff}
.stDownloadButton>button{background:#fff;color:#076f67;border-color:#078c80}
h1,h2,h3{color:#173541}hr{border-color:#d9e5e7}
</style>""", unsafe_allow_html=True)

def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)
def metric(label, value):
    st.markdown(f'<div class="metric"><small>{label}</small><strong>{value}</strong></div>', unsafe_allow_html=True)
def role_required(*roles):
    if st.session_state.user["role"] not in roles:
        st.error("Your role does not have permission to use this page.")
        st.stop()

if scalar("SELECT COUNT(*) FROM users") == 0:
    hero("Create your AttendAI administrator", "First-run setup is local and stored in the embedded encrypted application database.")
    with st.form("setup"):
        name = st.text_input("Administrator name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create administrator", use_container_width=True)
    if submitted:
        if len(password) < 10: st.error("Use at least 10 characters.")
        elif password != confirm: st.error("Passwords do not match.")
        elif not name or "@" not in email: st.error("Enter a name and valid email.")
        else:
            uid = execute("INSERT INTO users(email,name,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                          (email.lower().strip(), name.strip(), hash_password(password), "admin", utcnow()))
            audit(uid, "administrator.created", "user", uid)
            st.success("Administrator created. Sign in below.")
            st.rerun()
    st.stop()

if "user" not in st.session_state:
    hero("AttendAI Vision", "Self-contained computer-vision attendance—no external API or Docker required.")
    a,b,c = st.columns([1,1.2,1])
    with b:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            go = st.form_submit_button("Sign in", use_container_width=True)
        if go:
            rows = query("SELECT * FROM users WHERE email=? AND active=1", (email.lower().strip(),))
            if rows and verify_password(password, rows[0]["password_hash"]):
                st.session_state.user = rows[0]
                audit(rows[0]["id"], "user.login", "user", rows[0]["id"])
                st.rerun()
            else: st.error("Invalid email or password.")
    st.stop()

user = st.session_state.user
with st.sidebar:
    st.markdown("## ✦ AttendAI Vision")
    st.caption("COMPUTER VISION ATTENDANCE")
    st.markdown(f"**{user['name']}**  \n{user['role'].title()}")
    page = st.radio("Navigation", ["Dashboard","Live Recognition","Face Enrollment","Students","Courses","Sessions & Records","Reports","Users","Audit & Privacy"], label_visibility="collapsed")
    if cv_available():
        st.markdown('<div class="safe">● Local CV engine ready</div>', unsafe_allow_html=True)
    else:
        st.error(f"Vision engine unavailable: {CV_IMPORT_ERROR or 'OpenCV data missing'}")
    if st.button("Sign out", use_container_width=True):
        audit(user["id"], "user.logout", "user", user["id"])
        st.session_state.clear(); st.rerun()

if page == "Dashboard":
    hero("Attendance dashboard", "Live, database-backed metrics from this installation.")
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric("Students", scalar("SELECT COUNT(*) FROM students WHERE active=1"))
    with c2: metric("Face samples", scalar("SELECT COUNT(*) FROM face_embeddings"))
    with c3: metric("Sessions", scalar("SELECT COUNT(*) FROM sessions"))
    with c4:
        total=scalar("SELECT COUNT(*) FROM attendance"); present=scalar("SELECT COUNT(*) FROM attendance WHERE status IN ('present','late')")
        metric("Attendance rate", f"{(100*present/total if total else 0):.1f}%")
    st.subheader("Recent attendance")
    rows=query("""SELECT s.student_no,s.name,c.code,a.status,a.confidence,a.method,a.recorded_at
                  FROM attendance a JOIN students s ON s.id=a.student_id
                  LEFT JOIN sessions x ON x.id=a.session_id LEFT JOIN courses c ON c.id=x.course_id
                  ORDER BY a.recorded_at DESC LIMIT 20""")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Students":
    role_required("admin","teacher")
    hero("Student management", "Create students, manage consent, and assign courses.")
    with st.expander("Add student", expanded=True):
        with st.form("student"):
            a,b=st.columns(2); no=a.text_input("Student number"); name=b.text_input("Full name")
            a,b=st.columns(2); email=a.text_input("Email"); dept=b.text_input("Department")
            consent=st.checkbox("Biometric consent received")
            if st.form_submit_button("Add student"):
                try:
                    sid=execute("INSERT INTO students(student_no,name,email,department,consent) VALUES(?,?,?,?,?)",(no,name,email,dept,int(consent)))
                    audit(user["id"],"student.created","student",sid); st.success("Student added."); st.rerun()
                except Exception as e: st.error(f"Could not add student: {e}")
    st.dataframe(pd.DataFrame(query("SELECT id,student_no,name,email,department,consent,enrolled_at FROM students WHERE active=1 ORDER BY name")),use_container_width=True,hide_index=True)

elif page == "Courses":
    role_required("admin","teacher")
    hero("Courses", "Manage course catalog and class ownership.")
    with st.form("course"):
        a,b,c,d=st.columns(4); code=a.text_input("Code"); name=b.text_input("Course name"); dept=c.text_input("Department"); teacher=d.text_input("Teacher")
        if st.form_submit_button("Create course"):
            try:
                cid=execute("INSERT INTO courses(code,name,department,teacher) VALUES(?,?,?,?)",(code,name,dept,teacher))
                audit(user["id"],"course.created","course",cid); st.rerun()
            except Exception as e: st.error(str(e))
    st.dataframe(pd.DataFrame(query("SELECT * FROM courses ORDER BY code")),use_container_width=True,hide_index=True)

elif page == "Face Enrollment":
    role_required("admin","teacher")
    hero("Consent-based face enrollment", "Capture multiple high-quality samples. Only encrypted numerical embeddings are stored.")
    if not cv_available():
        st.error("OpenCV is not installed in this deployment. Reboot the app after its Python dependencies finish installing.")
        st.code("opencv-python-headless==4.11.0.86", language="text")
        st.stop()
    students=query("SELECT id,student_no,name,consent FROM students WHERE active=1 ORDER BY name")
    options={f"{s['student_no']} — {s['name']}":s for s in students}
    if not options: st.info("Create a student first."); st.stop()
    selected=options[st.selectbox("Student",options)]
    count=scalar("SELECT COUNT(*) FROM face_embeddings WHERE student_id=?",(selected["id"],))
    st.progress(min(count/10,1.0),text=f"{count}/10 enrolled samples")
    if not selected["consent"]: st.error("Biometric consent is not recorded for this student."); st.stop()
    capture=st.camera_input("Capture a sample")
    if capture:
        image=decode_image(capture.getvalue()); vector,info=detect_and_embed(image)
        if not info["ok"]: st.error(info["message"])
        else:
            st.image(annotate(image,info["box"],f"Quality {info['quality']:.0%}"))
            st.write(f"Brightness: {info['brightness']:.0f} · Sharpness: {info['blur']:.0f} · Eyes detected: {info['eyes']}")
            if st.button("Accept encrypted sample"):
                execute("INSERT INTO face_embeddings(student_id,encrypted_embedding,quality,created_at) VALUES(?,?,?,?)",
                        (selected["id"],encrypt_embedding(vector),info["quality"],utcnow()))
                execute("UPDATE students SET enrolled_at=? WHERE id=?",(utcnow(),selected["id"]))
                audit(user["id"],"biometric.enrolled","student",selected["id"],f"quality={info['quality']:.2f}")
                st.success("Encrypted sample saved."); st.rerun()
    if count and st.button("Delete all facial data",type="primary"):
        execute("DELETE FROM face_embeddings WHERE student_id=?",(selected["id"],)); execute("UPDATE students SET enrolled_at=NULL WHERE id=?",(selected["id"],))
        audit(user["id"],"biometric.deleted","student",selected["id"]); st.rerun()

elif page == "Live Recognition":
    role_required("admin","teacher")
    hero("Live recognition", "Detect, verify, and record a face once per active session.")
    if not cv_available():
        st.error("OpenCV is not installed in this deployment. Reboot the app after its Python dependencies finish installing.")
        st.stop()
    courses=query("SELECT * FROM courses ORDER BY code"); course_options={"Unassigned session":None}|{f"{c['code']} — {c['name']}":c["id"] for c in courses}
    active=query("SELECT * FROM sessions WHERE status='active' ORDER BY id DESC LIMIT 1")
    if not active:
        course_label=st.selectbox("Course",course_options); title=st.text_input("Session title","Attendance session"); room=st.text_input("Room")
        late=st.number_input("Late after minutes",0,120,10)
        if st.button("Start session"):
            sid=execute("INSERT INTO sessions(course_id,title,room,started_by,started_at,late_after) VALUES(?,?,?,?,?,?)",
                        (course_options[course_label],title,room,user["id"],utcnow(),late))
            audit(user["id"],"session.started","session",sid); st.rerun()
        st.stop()
    session=active[0]; st.success(f"Session #{session['id']} active · {session['title']}")
    frame=st.camera_input("Scan a face")
    if frame:
        image=decode_image(frame.getvalue()); probe,info=detect_and_embed(image)
        if not info["ok"]: st.error(info["message"])
        else:
            enrolled=query("""SELECT f.student_id,f.encrypted_embedding,s.student_no,s.name
                              FROM face_embeddings f JOIN students s ON s.id=f.student_id WHERE s.active=1""")
            scores={}
            names={}
            for row in enrolled:
                score=similarity(probe,decrypt_embedding(row["encrypted_embedding"]))
                if score>scores.get(row["student_id"],-1): scores[row["student_id"]]=score; names[row["student_id"]]=row
            best=max(scores,key=scores.get) if scores else None; score=scores.get(best,0)
            threshold=float(scalar("SELECT value FROM settings WHERE key='recognition_threshold'",default=".82"))
            if best is None or score<threshold:
                st.image(annotate(image,info["box"],f"UNKNOWN {score:.1%}",(30,60,220)))
                st.error("Unknown or uncertain face. No student was assigned.")
            else:
                match=names[best]; elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(session["started_at"])).total_seconds()/60
                status="late" if elapsed>session["late_after"] else "present"
                st.image(annotate(image,info["box"],f"{match['name']} {score:.1%}"))
                if st.button(f"Confirm {match['name']} as {status}"):
                    try:
                        execute("INSERT INTO attendance(session_id,student_id,status,confidence,method,recorded_at) VALUES(?,?,?,?,?,?)",
                                (session["id"],best,status,score,"facial_recognition",utcnow()))
                        audit(user["id"],"attendance.recognized","attendance",f"{session['id']}:{best}",f"confidence={score:.3f}")
                        st.success("Attendance recorded.")
                    except Exception: st.info("This student is already recorded for the session.")
    st.divider()
    fallback_students=query("SELECT id,student_no,name FROM students WHERE active=1 ORDER BY name")
    if fallback_students:
        labels={f"{s['student_no']} — {s['name']}":s["id"] for s in fallback_students}
        with st.form("fallback"):
            label=st.selectbox("Secure manual fallback",labels); reason=st.text_input("Required verification reason")
            if st.form_submit_button("Record manual attendance"):
                if len(reason)<5: st.error("Provide a reason.")
                else:
                    try:
                        execute("INSERT INTO attendance(session_id,student_id,status,method,recorded_at,modified_by,reason) VALUES(?,?,?,?,?,?,?)",
                                (session["id"],labels[label],"present","manual",utcnow(),user["id"],reason))
                        audit(user["id"],"attendance.manual","attendance",f"{session['id']}:{labels[label]}",reason); st.success("Recorded.")
                    except Exception: st.info("Already recorded.")
    if st.button("End session and calculate absences"):
        execute("UPDATE sessions SET status='ended',ended_at=? WHERE id=?",(utcnow(),session["id"]))
        enrolled_ids=query("SELECT student_id FROM enrollments WHERE course_id=?",(session["course_id"],)) if session["course_id"] else query("SELECT id student_id FROM students WHERE active=1")
        for s in enrolled_ids:
            try: execute("INSERT INTO attendance(session_id,student_id,status,method,recorded_at) VALUES(?,?,?,?,?)",(session["id"],s["student_id"],"absent","automatic",utcnow()))
            except Exception: pass
        audit(user["id"],"session.ended","session",session["id"]); st.rerun()

elif page == "Sessions & Records":
    hero("Sessions & attendance records", "Review server timestamps, confidence, method, and correction reasons.")
    records=query("""SELECT a.id,x.title,s.student_no,s.name,a.status,a.confidence,a.method,a.recorded_at,a.reason
                     FROM attendance a JOIN sessions x ON x.id=a.session_id JOIN students s ON s.id=a.student_id
                     ORDER BY a.recorded_at DESC""")
    st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True)
    role_required("admin","teacher")
    with st.form("correct"):
        rid=st.number_input("Attendance record ID",min_value=1,step=1); status=st.selectbox("Correct status",["present","late","absent","excused","pending_review"]); reason=st.text_input("Required reason")
        if st.form_submit_button("Apply correction"):
            if len(reason)<5: st.error("Provide a reason.")
            else:
                execute("UPDATE attendance SET status=?,modified_by=?,reason=? WHERE id=?",(status,user["id"],reason,rid))
                audit(user["id"],"attendance.corrected","attendance",rid,reason); st.success("Correction saved."); st.rerun()

elif page == "Reports":
    hero("Reports", "Export institution attendance data without exposing biometric embeddings.")
    rows=query("""SELECT s.student_no,s.name,c.code course,x.title,a.status,a.confidence,a.method,a.recorded_at,a.reason
                  FROM attendance a JOIN students s ON s.id=a.student_id JOIN sessions x ON x.id=a.session_id
                  LEFT JOIN courses c ON c.id=x.course_id ORDER BY a.recorded_at DESC""")
    df=pd.DataFrame(rows); st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("Download CSV",df.to_csv(index=False).encode(),"attendance-report.csv","text/csv",disabled=df.empty)

elif page == "Users":
    role_required("admin")
    hero("User and role management", "Create secure administrator, teacher, and student accounts.")
    with st.form("user"):
        a,b=st.columns(2); name=a.text_input("Name"); email=b.text_input("Email")
        a,b=st.columns(2); password=a.text_input("Temporary password",type="password"); role=b.selectbox("Role",["teacher","student","admin"])
        if st.form_submit_button("Create account"):
            try:
                uid=execute("INSERT INTO users(email,name,password_hash,role,created_at) VALUES(?,?,?,?,?)",(email.lower(),name,hash_password(password),role,utcnow()))
                audit(user["id"],"user.created","user",uid,f"role={role}"); st.success("Account created."); st.rerun()
            except Exception as e: st.error(str(e))
    st.dataframe(pd.DataFrame(query("SELECT id,email,name,role,active,created_at FROM users")),use_container_width=True,hide_index=True)

else:
    role_required("admin")
    hero("Audit and privacy", "Immutable activity history and biometric controls.")
    threshold=float(scalar("SELECT value FROM settings WHERE key='recognition_threshold'",default=".82"))
    new_threshold=st.slider("Recognition confidence threshold",0.50,0.99,threshold)
    retention=int(scalar("SELECT value FROM settings WHERE key='retention_days'",default="365"))
    new_retention=st.number_input("Embedding retention days",30,3650,retention)
    if st.button("Save privacy settings"):
        execute("UPDATE settings SET value=? WHERE key='recognition_threshold'",(str(new_threshold),))
        execute("UPDATE settings SET value=? WHERE key='retention_days'",(str(new_retention),))
        audit(user["id"],"settings.updated","settings",detail=f"threshold={new_threshold};retention={new_retention}"); st.success("Saved.")
    st.dataframe(pd.DataFrame(query("""SELECT a.created_at,u.email actor,a.action,a.entity,a.entity_id,a.detail
                                      FROM audit_logs a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 500""")),use_container_width=True,hide_index=True)

st.divider()
st.caption("AttendAI Vision · Local encrypted embeddings · No emotion, ethnicity, or demographic inference")
