"""Tests for LoginUser use case and POST /auth/login endpoint.

Verifies credential validation, token issuance, refresh token storage,
audit logging, and generic error messages (no user-enumeration).

Reference: authentication/tasks.md#4, requirements.md Req 1.3, 2.1
"""

import hashlib
from uuid import UUID

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app.identity.application.audit_service import AuditService
from app.identity.application.login_user import (
    InvalidCredentialsError,
    LoginUser,
    LoginUserInput,
)
from app.identity.domain.entities import (
    AuditAction,
    AuditLog,
    RefreshToken,
    User,
)
from app.main import app

# --- Test doubles ---


class InMemoryUserRepository:
    """Test double for UserRepository."""

    def __init__(self):
        self.users: list[User] = []

    def save(self, user: User) -> User:
        self.users.append(user)
        return user

    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self.users if u.email == email), None)

    def find_by_id(self, user_id: UUID) -> User | None:
        return next((u for u in self.users if u.id == user_id), None)


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


class InMemoryAuditLogRepository:
    """Test double for AuditLogRepository."""

    def __init__(self):
        self.entries: list[AuditLog] = []

    def save(self, entry: AuditLog) -> AuditLog:
        self.entries.append(entry)
        return entry

    def find_by_actor(self, actor_user_id: UUID) -> list[AuditLog]:
        return [e for e in self.entries if e.actor_user_id == actor_user_id]


# --- Fixtures for unit tests ---


def _create_hashed_user(email="maria@example.com", password="SecurePass123!"):
    """Create a User with a bcrypt-hashed password."""
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")
    return User(
        name="Maria Garcia",
        email=email,
        password_hash=password_hash,
    )


@pytest.fixture
def user_repo():
    repo = InMemoryUserRepository()
    repo.save(_create_hashed_user())
    return repo


@pytest.fixture
def refresh_token_repo():
    return InMemoryRefreshTokenRepository()


@pytest.fixture
def audit_repo():
    return InMemoryAuditLogRepository()


@pytest.fixture
def audit_service(audit_repo):
    return AuditService(repository=audit_repo)


@pytest.fixture
def use_case(user_repo, refresh_token_repo, audit_service):
    return LoginUser(
        user_repository=user_repo,
        refresh_token_repository=refresh_token_repo,
        audit_service=audit_service,
    )


# --- Unit tests for LoginUser use case ---


class TestLoginUserHappyPath:
    """Happy path: valid credentials return token pair."""

    def test_returns_access_token(self, use_case):
        input_dto = LoginUserInput(email="maria@example.com", password="SecurePass123!")
        result = use_case.execute(input_dto)

        assert result.access_token
        assert isinstance(result.access_token, str)

    def test_returns_refresh_token(self, use_case):
        input_dto = LoginUserInput(email="maria@example.com", password="SecurePass123!")
        result = use_case.execute(input_dto)

        assert result.refresh_token
        assert isinstance(result.refresh_token, str)

    def test_returns_bearer_token_type(self, use_case):
        input_dto = LoginUserInput(email="maria@example.com", password="SecurePass123!")
        result = use_case.execute(input_dto)

        assert result.token_type == "bearer"

    def test_stores_refresh_token_hash_in_repo(self, use_case, refresh_token_repo):
        input_dto = LoginUserInput(email="maria@example.com", password="SecurePass123!")
        result = use_case.execute(input_dto)

        assert len(refresh_token_repo.tokens) == 1
        stored = refresh_token_repo.tokens[0]
        expected_hash = hashlib.sha256(result.refresh_token.encode()).hexdigest()
        assert stored.token_hash == expected_hash

    def test_audit_log_created(self, use_case, audit_repo):
        input_dto = LoginUserInput(email="maria@example.com", password="SecurePass123!")
        use_case.execute(input_dto)

        assert len(audit_repo.entries) == 1
        entry = audit_repo.entries[0]
        assert entry.action == AuditAction.USER_LOGIN


class TestLoginUserWrongEmail:
    """Wrong email: raises InvalidCredentialsError (no user-enumeration)."""

    def test_nonexistent_email_raises(self, use_case):
        input_dto = LoginUserInput(email="unknown@example.com", password="SecurePass123!")

        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)

    def test_error_message_is_generic(self, use_case):
        input_dto = LoginUserInput(email="unknown@example.com", password="SecurePass123!")

        with pytest.raises(InvalidCredentialsError, match="invalid_credentials"):
            use_case.execute(input_dto)


class TestLoginUserWrongPassword:
    """Wrong password: raises InvalidCredentialsError (same error as wrong email)."""

    def test_wrong_password_raises(self, use_case):
        input_dto = LoginUserInput(email="maria@example.com", password="WrongPassword!")

        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)

    def test_error_message_is_generic(self, use_case):
        input_dto = LoginUserInput(email="maria@example.com", password="WrongPassword!")

        with pytest.raises(InvalidCredentialsError, match="invalid_credentials"):
            use_case.execute(input_dto)

    def test_no_tokens_stored_on_failure(self, use_case, refresh_token_repo):
        input_dto = LoginUserInput(email="maria@example.com", password="WrongPassword!")

        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)

        assert len(refresh_token_repo.tokens) == 0

    def test_no_audit_log_on_failure(self, use_case, audit_repo):
        input_dto = LoginUserInput(email="maria@example.com", password="WrongPassword!")

        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)

        assert len(audit_repo.entries) == 0


# --- Integration tests for POST /auth/login endpoint ---

client = TestClient(app)


def _register_user(
    email="maria@example.com",
    password="SecurePass123!",
    name="Maria Garcia",
):
    """Helper to register a user via the endpoint."""
    return client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
            "consent_policy_version": "1.0",
            "consent_purpose": "account_creation",
        },
    )


class TestLoginEndpointHappyPath:
    """POST /auth/login — successful login returns tokens."""

    def test_returns_200(self):
        _register_user()
        response = client.post(
            "/auth/login",
            json={"email": "maria@example.com", "password": "SecurePass123!"},
        )
        assert response.status_code == 200

    def test_returns_token_fields(self):
        _register_user()
        response = client.post(
            "/auth/login",
            json={"email": "maria@example.com", "password": "SecurePass123!"},
        )
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_access_token_is_valid_jwt(self):
        _register_user()
        response = client.post(
            "/auth/login",
            json={"email": "maria@example.com", "password": "SecurePass123!"},
        )
        data = response.json()

        # Access token should have 3 dot-separated parts (JWT format)
        parts = data["access_token"].split(".")
        assert len(parts) == 3


class TestLoginEndpointInvalidCredentials:
    """POST /auth/login — invalid credentials return 401."""

    def test_wrong_email_returns_401(self):
        _register_user()
        response = client.post(
            "/auth/login",
            json={"email": "unknown@example.com", "password": "SecurePass123!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_credentials"

    def test_wrong_password_returns_401(self):
        _register_user()
        response = client.post(
            "/auth/login",
            json={"email": "maria@example.com", "password": "WrongPassword!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_credentials"

    def test_same_error_for_email_and_password(self):
        """Both wrong email and wrong password produce identical error responses."""
        _register_user()

        resp_bad_email = client.post(
            "/auth/login",
            json={"email": "unknown@example.com", "password": "SecurePass123!"},
        )
        resp_bad_pass = client.post(
            "/auth/login",
            json={"email": "maria@example.com", "password": "WrongPassword!"},
        )

        assert resp_bad_email.status_code == resp_bad_pass.status_code == 401
        assert resp_bad_email.json()["detail"] == resp_bad_pass.json()["detail"]
