"""JWT token service — issues and verifies Access Tokens and Refresh Tokens.

Uses configuration from app.config (loaded from .env).
No business logic — token mechanics only.

Reference: ADR-0004 (Custom JWT Authentication)
"""

from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Issue a JWT access token for the given user_id."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token_value(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Issue a JWT refresh token for the given user_id."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.refresh_token_expire_days))
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_access_token(token: str) -> dict:
    """Verify and decode a JWT access token. Raises jwt.InvalidTokenError on failure."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return payload


def verify_refresh_token(token: str) -> dict:
    """Verify and decode a JWT refresh token. Raises jwt.InvalidTokenError on failure."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Not a refresh token")
    return payload
