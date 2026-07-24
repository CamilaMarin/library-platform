"""Tests for RefreshTokenUseCase and POST /auth/refresh endpoint.

Verifies token rotation atomicity, revocation enforcement, and error handling.

Reference: authentication/tasks.md#5, requirements.md Req 2.3, 2.5
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
from app.identity.application.refresh_token_use_case import (  # noqa: E402
    RefreshTokenUseCase,
    TokenRevokedError,
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


# --- Unit tests for RefreshTokenUseCase ---


class TestRefreshTokenHappyPath:
    """Happy path: valid refresh token returns new token pair, old token revoked."""

    def test_returns_new_access_token(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)
        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        result = use_case.execute(raw_token)

        assert result.access_token
        assert isinstance(result.access_token, str)
        # JWT format: 3 dot-separated parts
        assert len(result.access_token.split(".")) == 3

    def test_returns_new_refresh_token(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)
        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        result = use_case.execute(raw_token)

        assert result.refresh_token
        assert result.refresh_token != raw_token  # New token is different

    def test_returns_bearer_token_type(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)
        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        result = use_case.execute(raw_token)

        assert result.token_type == "bearer"

    def test_old_token_is_revoked(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)
        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        use_case.execute(raw_token)

        # The original token should be revoked
        assert repo.tokens[0].revoked is True

    def test_new_token_stored_in_repo(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)
        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        result = use_case.execute(raw_token)

        # Should have 2 tokens: old (revoked) + new
        assert len(repo.tokens) == 2
        new_token = repo.tokens[1]
        expected_hash = hashlib.sha256(result.refresh_token.encode()).hexdigest()
        assert new_token.token_hash == expected_hash
        assert new_token.revoked is False


class TestRefreshTokenRevoked:
    """Revoked token raises TokenRevokedError."""

    def test_revoked_token_raises(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, uid = _setup_valid_token(repo)

        # Revoke the token
        repo.tokens[0].revoked = True

        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        with pytest.raises(TokenRevokedError):
            use_case.execute(raw_token)


class TestRefreshTokenExpired:
    """Expired token raises TokenRevokedError."""

    def test_expired_token_raises(self):
        repo = InMemoryRefreshTokenRepository()
        uid = uuid4()
        raw_token = create_refresh_token_value(user_id=str(uid))
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # Store with an already-expired expires_at
        entity = RefreshToken(
            user_id=uid,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        repo.save(entity)

        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        with pytest.raises(TokenRevokedError):
            use_case.execute(raw_token)


class TestRefreshTokenNotFound:
    """Non-existent token (not in DB) raises TokenRevokedError."""

    def test_token_not_in_db_raises(self):
        repo = InMemoryRefreshTokenRepository()
        # Create a valid JWT but don't store it in the repo
        raw_token = create_refresh_token_value(user_id=str(uuid4()))

        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        with pytest.raises(TokenRevokedError):
            use_case.execute(raw_token)


class TestRefreshTokenReplay:
    """Replay: using the same token after rotation fails (already revoked)."""

    def test_replay_after_rotation_fails(self):
        repo = InMemoryRefreshTokenRepository()
        raw_token, _ = _setup_valid_token(repo)
        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        # First rotation succeeds
        use_case.execute(raw_token)

        # Second attempt with same token fails (already revoked)
        with pytest.raises(TokenRevokedError):
            use_case.execute(raw_token)


class TestRefreshTokenInvalidJWT:
    """Invalid JWT (garbage, wrong signature) raises TokenRevokedError."""

    def test_garbage_token_raises(self):
        repo = InMemoryRefreshTokenRepository()
        use_case = RefreshTokenUseCase(refresh_token_repository=repo)

        with pytest.raises(TokenRevokedError):
            use_case.execute("totally.not.a.valid.jwt")


# --- Integration tests for POST /auth/refresh endpoint ---


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


class TestRefreshEndpointHappyPath:
    """POST /auth/refresh — successful rotation returns new tokens."""

    def test_returns_200(self):
        tokens = _register_and_login()
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200

    def test_returns_new_token_pair(self):
        tokens = _register_and_login()
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # New tokens should differ from original
        assert data["refresh_token"] != tokens["refresh_token"]


class TestRefreshEndpointOldTokenInvalid:
    """POST /auth/refresh — using old token after refresh returns 401."""

    def test_old_token_returns_401(self):
        tokens = _register_and_login()
        old_refresh = tokens["refresh_token"]

        # Rotate once
        client.post("/auth/refresh", json={"refresh_token": old_refresh})

        # Try again with old token
        response = client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert response.status_code == 401
        assert response.json()["detail"] == "token_revoked"


class TestRefreshEndpointGarbageToken:
    """POST /auth/refresh — garbage token returns 401."""

    def test_garbage_token_returns_401(self):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "not.a.valid.jwt.token"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "token_revoked"
