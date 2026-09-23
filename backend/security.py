from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from backend.config import settings

_password_hash = PasswordHash.recommended()

PASSWORD_PATTERN = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
RESET_TOKEN_MINUTES = 30


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(password, password_hash)


def password_fingerprint(password_hash: str | None) -> str:
    return hashlib.sha256((password_hash or "").encode()).hexdigest()[:16]


def create_access_token(*, user_id: UUID, email: str, remember: bool = False) -> str:
    minutes = settings.jwt_remember_expire_minutes if remember else settings.jwt_expire_minutes
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_reset_token(*, user_id: UUID, email: str, password_hash: str | None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "typ": "reset",
        "pwd": password_fingerprint(password_hash),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=RESET_TOKEN_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    if payload.get("typ") == "reset":
        raise jwt.InvalidTokenError("Reset token cannot be used as access token")
    return payload


def decode_reset_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    if payload.get("typ") != "reset":
        raise jwt.InvalidTokenError("Not a reset token")
    return payload
