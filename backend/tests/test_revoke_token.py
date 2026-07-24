"""Tests for RevokeTokenUseCase and POST /auth/logout endpoint.

Verifies token revocation (logout) and information leakage prevention.

Reference: authentication/tasks.md#6, requirements.md Req 2.4, 2.5
Design: Property 5 (revocation enforcement)
"""

import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

# Override DATABASE_URL before any app import so the engine uses SQLite
os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.auth.jwt import create_refresh_token_value  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.identity.application.revoke_token_use_case import (  # noqa: E402
    RevokeTokenUseCase,
    TokenNotFoundError,
)
from app.identity.domain.entities import RefreshToken  # noqa: E402
from app.main import app  # noqa: E402

# --- Test doubles ---


class InMemoryRefreshTokenRepository:
    """Test double for RefreshTokenRepository."""

    def __init__(self):
        self.tokens: list[RefreshToken] = []

    def save(self, token: RefreshToken) -> RefreshToken:
        self.tokens.append(token)
        return token

    def find_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self.tokens if t.token_hash == token_hash), None)

    def find_active_by_user_id(self, user_id: UUID) -> list[RefreshToken]:
        return [t for t in self.tokens if t.user_id == user_id and t.is_usable]

    def revoke(self, token_id: UUID) -> None:
        for t in self.tokens:
            if t.id == token_id:
                t.revoked = True
                break


# --- Helpers ---


def _setup_valid_token(repo: InMemoryRefreshTokenRepository, user_id: UUID | None = None):
    """Create a valid refresh token and store its hash in the repo.

    Returns the raw token value and the user_id.
    """
    uid = user_id or uuid4()
    raw_token = create_refresh_token_value(user_id=str(uid))
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    entity = RefreshToken(
        user_id=uid,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    repo.save(entity)

    return raw_token, uid


# --- Unit tests for RevokeTokenUseCase ---


class TestRevokeTokenHappyPath:
    """Happy path: valid token gets revoked."""

    def test_token_is_revoked(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)
        use_case = RevokeTokenUseCase(refresh_token_repository=repo)

        use_case.execute(raw_token)

        assert repo.tokens[0].revoked is True

    def test_returns_none(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)
        use_case = RevokeTokenUseCase(refresh_token_repository=repo)

        result = use_case.execute(raw_token)

        assert result is None


class TestRevokeTokenAlreadyRevoked:
    """Already-revoked token raises TokenNotFoundError."""

    def test_already_revoked_raises(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)

        # Pre-revoke the token
        repo.tokens[0].revoked = True

        use_case = RevokeTokenUseCase(refresh_token_repository=repo)

        with pytest.raises(TokenNotFoundError):
            use_case.execute(raw_token)


class TestRevokeTokenNotFound:
    """Non-existent token (not in DB) raises TokenNotFoundError."""

    def test_token_not_in_db_raises(self):
        repo = InMemoryRefreshTokenRepository()
        # Create a valid JWT but don't store it in the repo
        raw_token = create_refresh_token_value(user_id=str(uuid4()))

        use_case = RevokeTokenUseCase(refresh_token_repository=repo)

        with pytest.raises(TokenNotFoundError):
            use_case.execute(raw_token)


class TestRevokeTokenInvalidJWT:
    """Invalid JWT (garbage) raises jwt.InvalidTokenError."""

    def test_garbage_token_raises(self):
        import jwt as pyjwt

        repo = InMemoryRefreshTokenRepository()
        use_case = RevokeTokenUseCase(refresh_token_repository=repo)

        with pytest.raises(pyjwt.InvalidTokenError):
            use_case.execute("totally.not.a.valid.jwt")


# --- Integration tests for POST /auth/logout endpoint ---


TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


def _register_and_login(
    email="maria@example.com",
    password="SecurePass123!",
):
    """Register a user and log in, returning the login response data."""
    client.post(
        "/auth/register",
        json={
            "name": "Maria Garcia",
            "email": email,
            "password": password,
            "consent_policy_version": "1.0",
            "consent_purpose": "account_creation",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    return login_response.json()


class TestLogoutEndpointHappyPath:
    """POST /auth/logout — successful logout returns 200."""

    def test_returns_200(self):
        tokens = _register_and_login()
        response = client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200

    def test_returns_logged_out_detail(self):
        tokens = _register_and_login()
        response = client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.json()["detail"] == "logged_out"


class TestLogoutThenRefreshFails:
    """After logout, refresh with old token returns 401 (revocation enforcement)."""

    def test_refresh_after_logout_returns_401(self):
        tokens = _register_and_login()
        refresh_token = tokens["refresh_token"]

        # Logout
        client.post("/auth/logout", json={"refresh_token": refresh_token})

        # Try to refresh with the revoked token
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401
        assert response.json()["detail"] == "token_revoked"


class TestLogoutGarbageToken:
    """POST /auth/logout with garbage token still returns 200 (no info leakage)."""

    def test_garbage_token_returns_200(self):
        response = client.post(
            "/auth/logout",
            json={"refresh_token": "not.a.valid.jwt.token"},
        )
        assert response.status_code == 200
        assert response.json()["detail"] == "logged_out"


class TestLogoutAlreadyRevokedToken:
    """POST /auth/logout with already-revoked token still returns 200."""

    def test_already_revoked_returns_200(self):
        tokens = _register_and_login()
        refresh_token = tokens["refresh_token"]

        # Logout once
        response1 = client.post("/auth/logout", json={"refresh_token": refresh_token})
        assert response1.status_code == 200

        # Logout again with same token
        response2 = client.post("/auth/logout", json={"refresh_token": refresh_token})
        assert response2.status_code == 200
        assert response2.json()["detail"] == "logged_out"
