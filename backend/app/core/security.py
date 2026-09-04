import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from argon2 import PasswordHasher
from app.core.config import settings


ph = PasswordHasher()


def create_access_token(user_id: str, session_id: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "sid": session_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt.secret, algorithm=settings.jwt.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.jwt.secret, algorithms=[settings.jwt.algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise ValueError("Token expired") from e
    except jwt.InvalidTokenError as e:
        raise ValueError("Invalid token") from e


import uuid

def generate_refresh_token() -> tuple[str, str]:
    token_id = str(uuid.uuid4())
    secret = secrets.token_urlsafe(32)
    return token_id, secret


def hash_refresh_token(secret: str) -> str:
    return ph.hash(secret)


def verify_refresh_token(token_hash: str, secret: str) -> bool:
    try:
        ph.verify(token_hash, secret)
        return True
    except Exception:
        return False


def encode_refresh_token(token_id: str, secret: str) -> str:
    return f"{token_id}.{secret}"


def decode_refresh_token(token: str) -> tuple[str, str] | None:
    parts = token.split(".", 1)
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def constant_time_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(a, b)