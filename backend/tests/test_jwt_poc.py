"""Proof-of-concept test for JWT utility functions (M-1 Architecture Validation).

Validates that PyJWT token issuance and verification works correctly.
No business logic — just stack validation.

Reference: ADR-0004
"""

import jwt as pyjwt
import pytest

from app.auth.jwt import create_access_token, verify_access_token


def test_create_and_verify_token():
    """A created token can be verified and contains the correct user_id."""
    token = create_access_token(user_id="user-123")
    payload = verify_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_expired_token_is_rejected():
    """An expired token raises an error on verification."""
    from datetime import timedelta

    token = create_access_token(user_id="user-123", expires_delta=timedelta(seconds=-1))
    with pytest.raises(pyjwt.ExpiredSignatureError):
        verify_access_token(token)


def test_tampered_token_is_rejected():
    """A token with a modified payload is rejected."""
    token = create_access_token(user_id="user-123")
    # Tamper with the token
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_access_token(tampered)
