# AttendAI — AI-Powered Smart Attendance

Production-oriented attendance platform for schools, universities, and offices. It combines a responsive role-based portal, FastAPI services, PostgreSQL persistence, real-time session updates, consent-based encrypted face embeddings, audit trails, and secure manual/QR fallback.

## Architecture

```text
Browser (React/Vinext) ── REST + WebSocket ── FastAPI
                                                  ├── PostgreSQL
Classroom camera ── quality/liveness/model adapter ├── encrypted embeddings
                                                  └── audit + reports
```

The recognition endpoint intentionally accepts only confirmed model results. A production camera worker should use InsightFace `buffalo_l`, require one face during enrollment, normalize its vector, run passive/active liveness, and submit only after three consecutive frames exceed the configured threshold. Scores below the threshold are `unknown`; they are never assigned to the nearest student.

## Quick start

1. Copy `.env.example` to `.env`. Replace `JWT_SECRET` and generate `EMBEDDING_KEY` with:
   `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. Run `docker compose up --build`.
3. Open the web app at `http://localhost:3000`, API docs at `http://localhost:8000/docs`.

For local development, run `npm install && npm run dev` for the portal and install `backend/requirements.txt`, then run `uvicorn app.main:app --reload` from `backend`.

## Security and privacy

- Argon2 password hashes; short-lived JWT access tokens and rotating-ready refresh tokens.
- Face vectors encrypted with Fernet; no endpoint returns embeddings.
- Explicit consent is required. Enrollment/deletion and every attendance correction are audited.
- Unique database constraint prevents duplicate attendance per student/session.
- Server timestamps are authoritative. Manual corrections require a reason.
- Secure headers, input bounds, role checks, soft-deletion fields, and least-privilege API surfaces are included.
- Deploy behind TLS, store secrets in a secret manager, restrict CORS, rotate keys, configure retention, and use PostgreSQL encryption/backups.
- The system does not infer emotion, ethnicity, gender, age, or other demographics.

## Recognition integration

Install OpenCV and InsightFace in a separate GPU-capable worker. Implement adapters for frame quality (brightness, blur, pose), multi-face rejection during enrollment, tracker IDs, cosine similarity, duplicate-vector search, multi-frame confirmation, and a certified liveness model. Keep sessions active when this worker is unavailable; teachers can use the QR/manual fallback.

## Tests

- `npm run build` validates the portal.
- `pytest backend/tests` validates attendance boundaries, percentages, and unknown-face threshold behavior.
- Extend with PostgreSQL-backed API integration and authorization tests in CI.

## Production checklist

Run Alembic migrations, create the first administrator via a one-time secret-backed command, configure HTTPS and trusted origins, use Redis-backed rate limiting, connect object storage for generated reports, configure monitoring, review biometric retention with counsel, and conduct a spoofing/security assessment before live biometric use.
