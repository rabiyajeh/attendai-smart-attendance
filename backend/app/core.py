from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from jose import jwt
from pwdlib import PasswordHash
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://attendai:attendai@db:5432/attendai"
    jwt_secret: str = "change-me-in-production"
    embedding_key: str = ""
    access_minutes: int = 15
    refresh_days: int = 7
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def settings(): return Settings()

password_hash = PasswordHash.recommended()
def hash_password(value: str) -> str: return password_hash.hash(value)
def verify_password(value: str, hashed: str) -> bool: return password_hash.verify(value, hashed)
def token(subject: str, role: str, refresh=False) -> str:
    ttl = timedelta(days=settings().refresh_days) if refresh else timedelta(minutes=settings().access_minutes)
    return jwt.encode({"sub":subject, "role":role, "type":"refresh" if refresh else "access",
                       "exp":datetime.now(timezone.utc)+ttl}, settings().jwt_secret, algorithm="HS256")
def cipher() -> Fernet:
    if not settings().embedding_key:
        raise RuntimeError("EMBEDDING_KEY is required for biometric enrollment")
    return Fernet(settings().embedding_key.encode())
