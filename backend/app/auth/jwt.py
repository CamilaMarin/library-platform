"""JWT utility functions — proof of concept for M-1 Architecture Validation.

This module demonstrates JWT token issuance and verification works with the
chosen stack (PyJWT). No business logic — that belongs to M1 (Authentication).

Reference: ADR-0004 (Custom JWT Authentication)
"""

from datetime import datetime, timedelta, timezone

import jwt

# PoC secret — will be replaced by a proper secret management in M1
_SECRET_KEY = "entrelineas-dev-secret-replace-in-production"
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Issue a JWT access token for the given user_id."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def verify_access_token(token: str) -> dict:
    """Verify and decode a JWT access token. Raises jwt.InvalidTokenError on failure."""
    payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return payload
