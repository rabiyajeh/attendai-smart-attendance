# AttendAI — Python Smart Attendance

AttendAI is a Python-first attendance platform for schools, universities, and offices. The user interface runs on Streamlit, the API runs on FastAPI, and persistent records are stored in PostgreSQL.

## Stack

- Streamlit and pandas for the responsive role-based web portal
- FastAPI for authenticated REST and WebSocket services
- PostgreSQL and SQLAlchemy for durable attendance data
- InsightFace/OpenCV-compatible recognition worker contract
- Argon2 passwords, JWT authorization, and encrypted facial embeddings
- Docker Compose for local and server deployment

This project is not configured for ChatGPT Sites hosting. Deploy the Streamlit container to Streamlit Community Cloud, Render, Railway, Fly.io, AWS, Azure, or your own Docker server.

## Run with Docker

1. Copy `.env.example` to `.env`.
2. Replace `JWT_SECRET`.
3. Generate `EMBEDDING_KEY`:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. Start the stack:

   ```bash
   docker compose up --build
   ```

Open:

- Streamlit portal: `http://localhost:8501`
- FastAPI documentation: `http://localhost:8000/docs`

## Local Python development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
streamlit run streamlit_app.py
```

Set `API_URL` when the API is not on `http://localhost:8000`.

## Recognition integration

Use a separate GPU-capable OpenCV/InsightFace worker. Enrollment must validate consent, lighting, blur, pose, and single-face framing before normalizing and encrypting embeddings. Live recognition must include tracking, liveness, duplicate prevention, and at least three consecutive frames above the configured threshold. Uncertain faces remain unknown.

## Privacy

- Raw face images are not stored by default.
- Facial embeddings are encrypted and never returned through frontend APIs.
- Enrollment and deletion require authorization and create audit events.
- Manual corrections require a reason.
- One database record per student/session is enforced.
- Secure QR and manual verification remain available.
- No emotion, ethnicity, or demographic inference is performed.

## Tests

```bash
python -m pytest backend/tests -q
```

The tests cover attendance boundaries, percentages, and recognition-threshold behavior. Add PostgreSQL integration tests and a certified liveness assessment before biometric production use.
