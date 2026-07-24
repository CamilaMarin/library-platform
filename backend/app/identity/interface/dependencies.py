"""Shared FastAPI dependencies for authenticated endpoints.

Reference: authentication/design.md, ADR-0004
"""

from uuid import UUID

import jwt
from fastapi import Header, HTTPException, status

from app.auth.jwt import verify_access_token


def get_current_user_id(authorization: str = Header(...)) -> UUID:
    """Extract and verify user_id from the Authorization header.

    Expects: Authorization: Bearer <access_token>
    Returns the user_id (UUID) from the token payload.
    Raises 401 if header is missing, malformed, or token is invalid/expired.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_authorization_header",
        )

    token = authorization[len("Bearer "):]

    try:
        payload = verify_access_token(token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_or_expired_token",
        )

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token_payload",
        )

    return user_id
