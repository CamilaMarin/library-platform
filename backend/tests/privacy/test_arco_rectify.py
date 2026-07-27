"""Tests for ARCO rectification: PATCH /users/me and OpposeDataProcessing.

Covers:
- RectifyUserData use case (unit tests)
- OpposeDataProcessing use case (unit tests)
- Endpoint integration tests

Reference: privacy/requirements.md Req 1.2
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.identity.application.audit_service import AuditService
from app.identity.application.oppose_data_processing import OpposeDataProcessing
from app.identity.application.rectify_user_data import (
    EmailAlreadyTakenError,
    InvalidEmailError,
    NoFieldsProvidedError,
    RectifyUserData,
)
from app.identity.domain.entities import AuditAction, User
from app.identity.infrastructure.repositories import (
    SqlAuditLogRepository,
    SqlUserRepository,
)
from app.main import app
from tests.conftest import TestSession

client = TestClient(app)


def _register_and_login(email="rectify@example.com", name="Test User"):
    """Helper: register a user and return (user_id, access_token)."""
    reg_response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "SecurePass123!",
            "consent_policy_version": "1.0",
            "consent_purpose": "account_creation",
        },
    )
    user_id = reg_response.json()["id"]

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    access_token = login_response.json()["access_token"]

    return user_id, access_token


# --- Unit tests for RectifyUserData ---


class TestRectifyUserDataUseCase:
    """Unit tests for RectifyUserData use case."""

    def _get_session(self):
        return TestSession()

    def test_successful_name_update(self):
        """Rectify updates user name when provided."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            user_id = uuid4()
            user = User(id=user_id, name="Old Name", email="name@test.com", password_hash="hashed")
            user_repo.save(user)
            db.commit()

            use_case = RectifyUserData(
                user_repository=user_repo,
                audit_service=audit_service,
            )
            result = use_case.execute(user_id=user_id, new_name="New Name")
            db.commit()

            assert result.name == "New Name"
            assert result.email == "name@test.com"

            # Verify user was actually updated in DB
            updated_user = user_repo.find_by_id(user_id)
            assert updated_user.name == "New Name"
        finally:
            db.close()

    def test_successful_email_update(self):
        """Rectify updates user email when provided."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            user_id = uuid4()
            user = User(id=user_id, name="User", email="old@test.com", password_hash="hashed")
            user_repo.save(user)
            db.commit()

            use_case = RectifyUserData(
                user_repository=user_repo,
                audit_service=audit_service,
            )
            result = use_case.execute(user_id=user_id, new_email="new@test.com")
            db.commit()

            assert result.email == "new@test.com"
            assert result.name == "User"

            # Verify user was actually updated in DB
            updated_user = user_repo.find_by_id(user_id)
            assert updated_user.email == "new@test.com"
        finally:
            db.close()

    def test_email_already_taken_returns_error(self):
        """Rectify raises EmailAlreadyTakenError when email is in use."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            # Create two users
            user1_id = uuid4()
            user1 = User(id=user1_id, name="User1", email="user1@test.com", password_hash="hashed")
            user_repo.save(user1)

            user2_id = uuid4()
            user2 = User(id=user2_id, name="User2", email="user2@test.com", password_hash="hashed")
            user_repo.save(user2)
            db.commit()

            use_case = RectifyUserData(
                user_repository=user_repo,
                audit_service=audit_service,
            )

            # Try to change user1's email to user2's email
            with pytest.raises(EmailAlreadyTakenError):
                use_case.execute(user_id=user1_id, new_email="user2@test.com")
        finally:
            db.close()

    def test_no_fields_provided_returns_error(self):
        """Rectify raises NoFieldsProvidedError when no fields given."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            user_id = uuid4()
            user = User(id=user_id, name="User", email="nofields@test.com", password_hash="hashed")
            user_repo.save(user)
            db.commit()

            use_case = RectifyUserData(
                user_repository=user_repo,
                audit_service=audit_service,
            )

            with pytest.raises(NoFieldsProvidedError):
                use_case.execute(user_id=user_id)
        finally:
            db.close()

    def test_audit_log_created(self):
        """Rectify creates an audit log entry with ARCO_RECTIFY action."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            user_id = uuid4()
            user = User(id=user_id, name="Audit", email="audit@test.com", password_hash="hashed")
            user_repo.save(user)
            db.commit()

            use_case = RectifyUserData(
                user_repository=user_repo,
                audit_service=audit_service,
            )
            use_case.execute(user_id=user_id, new_name="Audited Name")
            db.commit()

            logs = audit_repo.find_by_actor(user_id)
            assert len(logs) == 1
            assert logs[0].action == AuditAction.ARCO_RECTIFY
            assert f"user:{user_id}:rectify" in logs[0].affected_entity
        finally:
            db.close()

    def test_invalid_email_format_returns_error(self):
        """Rectify raises InvalidEmailError for malformed email."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            user_id = uuid4()
            user = User(id=user_id, name="User", email="valid@test.com", password_hash="hashed")
            user_repo.save(user)
            db.commit()

            use_case = RectifyUserData(
                user_repository=user_repo,
                audit_service=audit_service,
            )

            with pytest.raises(InvalidEmailError):
                use_case.execute(user_id=user_id, new_email="not-an-email")
        finally:
            db.close()


# --- Unit tests for OpposeDataProcessing ---


class TestOpposeDataProcessingUseCase:
    """Unit tests for OpposeDataProcessing use case."""

    def _get_session(self):
        return TestSession()

    def test_successful_opposition(self):
        """Oppose registers the purpose in privacy_settings."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            user_id = uuid4()
            user = User(id=user_id, name="User", email="oppose@test.com", password_hash="hashed")
            user_repo.save(user)
            db.commit()

            use_case = OpposeDataProcessing(
                user_repository=user_repo,
                audit_service=audit_service,
            )
            result = use_case.execute(user_id=user_id, processing_purpose="marketing")
            db.commit()

            assert result.opposed is True
            assert result.processing_purpose == "marketing"

            # Verify privacy_settings updated
            updated_user = user_repo.find_by_id(user_id)
            assert "marketing" in updated_user.privacy_settings.get("opposed_purposes", [])
        finally:
            db.close()

    def test_oppose_audit_log_created(self):
        """Oppose creates an audit log entry with ARCO_OPPOSE action."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            user_id = uuid4()
            user = User(id=user_id, name="User", email="oppaudit@test.com", password_hash="hashed")
            user_repo.save(user)
            db.commit()

            use_case = OpposeDataProcessing(
                user_repository=user_repo,
                audit_service=audit_service,
            )
            use_case.execute(user_id=user_id, processing_purpose="analytics")
            db.commit()

            logs = audit_repo.find_by_actor(user_id)
            assert len(logs) == 1
            assert logs[0].action == AuditAction.ARCO_OPPOSE
            assert "oppose:analytics" in logs[0].affected_entity
        finally:
            db.close()


# --- Integration tests for endpoints ---


class TestRectifyEndpoint:
    """PATCH /users/me — integration tests."""

    def test_update_name(self):
        """Rectify updates user name via endpoint."""
        user_id, token = _register_and_login(email="patch1@test.com")

        response = client.patch(
            "/users/me",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "patch1@test.com"

    def test_update_email(self):
        """Rectify updates user email via endpoint."""
        user_id, token = _register_and_login(email="patch2@test.com")

        response = client.patch(
            "/users/me",
            json={"email": "patched2@test.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "patched2@test.com"

    def test_no_fields_returns_400(self):
        """Rectify returns 400 when no fields provided."""
        _, token = _register_and_login(email="patch3@test.com")

        response = client.patch(
            "/users/me",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "no_fields_provided"

    def test_email_conflict_returns_409(self):
        """Rectify returns 409 when email is already taken."""
        _register_and_login(email="existing@test.com")
        _, token = _register_and_login(email="patch4@test.com")

        response = client.patch(
            "/users/me",
            json={"email": "existing@test.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "email_already_taken"

    def test_requires_auth(self):
        """Rectify requires a valid Authorization header."""
        response = client.patch("/users/me", json={"name": "X"})
        assert response.status_code == 422


class TestOpposeEndpoint:
    """POST /users/me/oppose — integration tests."""

    def test_oppose_purpose(self):
        """Oppose registers opposition via endpoint."""
        _, token = _register_and_login(email="oppose1@test.com")

        response = client.post(
            "/users/me/oppose",
            json={"purpose": "marketing"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["processing_purpose"] == "marketing"
        assert data["opposed"] is True

    def test_requires_auth(self):
        """Oppose requires a valid Authorization header."""
        response = client.post("/users/me/oppose", json={"purpose": "marketing"})
        assert response.status_code == 422
