# AttendAI Vision

A self-contained computer-vision attendance system built with Python, Streamlit, OpenCV, SQLite, pandas, and encrypted facial embeddings. It runs without FastAPI, PostgreSQL, or Docker; Docker is optional for deployment.

## Included workflows

- First-run administrator setup and local authentication
- Administrator, teacher, and student roles
- Student, user, course, and session management
- Consent-gated facial enrollment with lighting, blur, face-count, and eye checks
- Multiple encrypted face samples per student
- OpenCV face detection and privacy-preserving numerical embeddings
- Confidence-threshold recognition that leaves uncertain faces unknown
- Present/late rules, duplicate prevention, automated absences, and manual fallback
- Attendance correction with a required reason
- CSV reports, audit logs, recognition confidence, and privacy controls
- Embedded SQLite persistence in `.data/attendai.db`
- No raw enrollment photographs stored by default

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open `http://localhost:8501`. On first launch, create the administrator account in the setup screen.

## Run with Docker

```bash
docker compose up --build
```

The named Docker volume preserves users, courses, attendance, audit logs, settings, and encrypted embeddings.

## Recognition approach

The built-in engine uses OpenCV Haar detection, quality gates, histogram equalization, low-frequency DCT facial descriptors, encrypted storage, and cosine similarity. It is designed to provide a complete local demonstration without external model downloads.

For high-security production use, replace `attendai/vision.py` with InsightFace or a certified FaceNet deployment and add a dedicated anti-spoofing model. Facial recognition should never be the only attendance option; verified manual fallback remains available.

## Privacy and security

- Passwords use salted `scrypt`.
- Facial descriptors are encrypted at rest with a locally generated Fernet key.
- Consent is required before enrollment.
- Biometric enrollment and deletion create audit events.
- Embeddings are never included in reports or UI tables.
- Unknown and uncertain faces are never assigned to the nearest student.
- No emotion, ethnicity, gender, age, or demographic inference is performed.

Back up `.data/attendai.db` and `.data/embedding.key` together. Losing the encryption key makes stored facial descriptors unrecoverable.

## Tests

```bash
python -m pytest backend/tests -q
python -m py_compile streamlit_app.py attendai/database.py attendai/vision.py
```
