import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.getenv("ATTENDAI_DATA_DIR", ".data"))
DB_PATH = DATA_DIR / "attendai.db"

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','teacher','student')),
 active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS students(
 id INTEGER PRIMARY KEY, student_no TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 email TEXT, department TEXT, consent INTEGER NOT NULL DEFAULT 0,
 enrolled_at TEXT, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS courses(
 id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 department TEXT, teacher TEXT);
CREATE TABLE IF NOT EXISTS enrollments(
 student_id INTEGER NOT NULL REFERENCES students(id), course_id INTEGER NOT NULL REFERENCES courses(id),
 PRIMARY KEY(student_id,course_id));
CREATE TABLE IF NOT EXISTS face_embeddings(
 id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES students(id),
 encrypted_embedding BLOB NOT NULL, quality REAL NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(
 id INTEGER PRIMARY KEY, course_id INTEGER REFERENCES courses(id), title TEXT NOT NULL,
 room TEXT, started_by INTEGER REFERENCES users(id), started_at TEXT NOT NULL,
 ended_at TEXT, late_after INTEGER NOT NULL DEFAULT 10, status TEXT NOT NULL DEFAULT 'active');
CREATE TABLE IF NOT EXISTS attendance(
 id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES sessions(id),
 student_id INTEGER NOT NULL REFERENCES students(id), status TEXT NOT NULL,
 confidence REAL, method TEXT NOT NULL, recorded_at TEXT NOT NULL,
 modified_by INTEGER REFERENCES users(id), reason TEXT,
 UNIQUE(session_id,student_id));
CREATE TABLE IF NOT EXISTS audit_logs(
 id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id), action TEXT NOT NULL,
 entity TEXT NOT NULL, entity_id TEXT, detail TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
INSERT OR IGNORE INTO settings VALUES('recognition_threshold','0.82');
INSERT OR IGNORE INTO settings VALUES('retention_days','365');
INSERT OR IGNORE INTO settings VALUES('low_attendance_threshold','75');
"""

def utcnow(): return datetime.now(timezone.utc).isoformat()

@contextmanager
def connection():
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        db.commit()
    finally:
        db.close()

def init_db():
    with connection() as db:
        db.executescript(SCHEMA)

def query(sql, params=()):
    with connection() as db:
        return [dict(row) for row in db.execute(sql, params).fetchall()]

def execute(sql, params=()):
    with connection() as db:
        cur = db.execute(sql, params)
        return cur.lastrowid

def scalar(sql, params=(), default=0):
    rows = query(sql, params)
    return next(iter(rows[0].values())) if rows else default

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}:{digest.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":")
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return secrets.compare_digest(actual.hex(), digest_hex)
    except ValueError:
        return False

def audit(actor_id, action, entity, entity_id=None, detail=None):
    execute("INSERT INTO audit_logs(actor_id,action,entity,entity_id,detail,created_at) VALUES(?,?,?,?,?,?)",
            (actor_id, action, entity, str(entity_id) if entity_id else None, detail, utcnow()))
