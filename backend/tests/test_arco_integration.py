"""Tests for ARCO integration: GET /users/me/export and DELETE /users/me.

Covers:
- ExportUserData use case (unit tests)
- DeleteUserAccount use case (unit tests)
- Endpoint integration tests (register -> export / delete)
- Auth enforcement on both endpoints

Reference: authentication/requirements.md Req 4.1, 4.2
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.identity.application.audit_service import AuditService
from app.identity.application.delete_user_account import (
    DeleteUserAccount,
)
from app.identity.application.delete_user_account import (
    UserNotFoundError as DeleteUserNotFoundError,
)
from app.identity.application.export_user_data import (
    ExportUserData,
)
from app.identity.application.export_user_data import (
    UserNotFoundError as ExportUserNotFoundError,
)
from app.identity.domain.entities import (
    AuditAction,
    DataConsent,
    DataProcessingRecord,
    FamilyGroup,
    GroupMembership,
    MembershipStatus,
    RefreshToken,
    User,
)
from app.identity.infrastructure.repositories import (
    SqlAuditLogRepository,
    SqlDataConsentRepository,
    SqlDataProcessingRecordRepository,
    SqlFamilyGroupRepository,
    SqlGroupMembershipRepository,
    SqlRefreshTokenRepository,
    SqlUserRepository,
)
from app.main import app
from tests.conftest import TestSession

client = TestClient(app)


def _register_and_login(email="test@example.com", name="Test User"):
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


# --- Unit tests for ExportUserData ---


class TestExportUserDataUseCase:
    """Unit tests for ExportUserData use case."""

    def _get_session(self):
        return TestSession()

    def test_happy_path_returns_all_user_data(self):
        """Export returns user profile, consents, memberships, processing records."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            consent_repo = SqlDataConsentRepository(db)
            membership_repo = SqlGroupMembershipRepository(db)
            processing_record_repo = SqlDataProcessingRecordRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            # Create user
            user_id = uuid4()
            user = User(id=user_id, name="María", email="maria@test.com", password_hash="hashed")
            user_repo.save(user)

            # Create consent
            consent = DataConsent(
                user_id=user_id, policy_version="1.0", purpose="account_creation"
            )
            consent_repo.save(consent)

            # Create processing record
            record = DataProcessingRecord(
                user_id=user_id,
                data_type="email",
                purpose="authentication",
                legal_basis="consent",
            )
            processing_record_repo.save(record)

            # Create membership
            group_id = uuid4()
            group_repo = SqlFamilyGroupRepository(db)
            group = FamilyGroup(id=group_id, name="Test Family")
            group_repo.save(group)

            membership = GroupMembership(
                group_id=group_id, user_id=user_id, status=MembershipStatus.ACCEPTED
            )
            membership_repo.save(membership)

            db.commit()

            # Execute use case
            use_case = ExportUserData(
                user_repository=user_repo,
                consent_repository=consent_repo,
                membership_repository=membership_repo,
                processing_record_repository=processing_record_repo,
                audit_service=audit_service,
            )
            result = use_case.execute(user_id)
            db.commit()

            # Verify user data (no password_hash)
            assert result.user.name == "María"
            assert result.user.email == "maria@test.com"
            assert not hasattr(result.user, "password_hash")

            # Verify consents
            assert len(result.consents) == 1
            assert result.consents[0].policy_version == "1.0"

            # Verify memberships
            assert len(result.memberships) == 1
            assert result.memberships[0].group_id == group_id

            # Verify processing records
            assert len(result.processing_records) == 1
            assert result.processing_records[0].data_type == "email"
        finally:
            db.close()

    def test_user_not_found_raises_error(self):
        """Export raises UserNotFoundError for non-existent user."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            consent_repo = SqlDataConsentRepository(db)
            membership_repo = SqlGroupMembershipRepository(db)
            processing_record_repo = SqlDataProcessingRecordRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            use_case = ExportUserData(
                user_repository=user_repo,
                consent_repository=consent_repo,
                membership_repository=membership_repo,
                processing_record_repository=processing_record_repo,
                audit_service=audit_service,
            )

            with pytest.raises(ExportUserNotFoundError):
                use_case.execute(uuid4())
        finally:
            db.close()

    def test_audit_log_created_with_arco_request(self):
        """Export creates an audit log entry with ARCO_REQUEST action."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            consent_repo = SqlDataConsentRepository(db)
            membership_repo = SqlGroupMembershipRepository(db)
            processing_record_repo = SqlDataProcessingRecordRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            # Create user
            user_id = uuid4()
            user = User(
                id=user_id, name="Test", email="audit@test.com", password_hash="hashed"
            )
            user_repo.save(user)
            db.commit()

            use_case = ExportUserData(
                user_repository=user_repo,
                consent_repository=consent_repo,
                membership_repository=membership_repo,
                processing_record_repository=processing_record_repo,
                audit_service=audit_service,
            )
            use_case.execute(user_id)
            db.commit()

            # Check audit log
            logs = audit_repo.find_by_actor(user_id)
            assert len(logs) == 1
            assert logs[0].action == AuditAction.ARCO_REQUEST
            assert f"user:{user_id}:export" in logs[0].affected_entity
        finally:
            db.close()


# --- Unit tests for DeleteUserAccount ---


class TestDeleteUserAccountUseCase:
    """Unit tests for DeleteUserAccount use case."""

    def _get_session(self):
        return TestSession()

    def test_happy_path_deletes_all_data(self):
        """Delete removes user, consents, memberships, processing records."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            consent_repo = SqlDataConsentRepository(db)
            membership_repo = SqlGroupMembershipRepository(db)
            processing_record_repo = SqlDataProcessingRecordRepository(db)
            refresh_token_repo = SqlRefreshTokenRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            # Create user with associated data
            user_id = uuid4()
            user = User(
                id=user_id, name="ToDelete", email="delete@test.com", password_hash="hashed"
            )
            user_repo.save(user)

            consent = DataConsent(
                user_id=user_id, policy_version="1.0", purpose="account_creation"
            )
            consent_repo.save(consent)

            record = DataProcessingRecord(
                user_id=user_id,
                data_type="email",
                purpose="auth",
                legal_basis="consent",
            )
            processing_record_repo.save(record)

            group_id = uuid4()
            membership = GroupMembership(
                group_id=group_id, user_id=user_id, status=MembershipStatus.ACCEPTED
            )
            membership_repo.save(membership)

            db.commit()

            # Execute delete
            use_case = DeleteUserAccount(
                user_repository=user_repo,
                refresh_token_repository=refresh_token_repo,
                membership_repository=membership_repo,
                consent_repository=consent_repo,
                processing_record_repository=processing_record_repo,
                audit_service=audit_service,
            )
            use_case.execute(user_id)
            db.commit()

            # Verify everything is deleted
            assert user_repo.find_by_id(user_id) is None
            assert consent_repo.find_by_user_id(user_id) is None
            assert membership_repo.find_by_user_id(user_id) == []
            assert processing_record_repo.find_by_user_id(user_id) == []
        finally:
            db.close()

    def test_refresh_tokens_revoked(self):
        """Delete revokes all active refresh tokens for the user."""
        db = self._get_session()
        try:
            from datetime import datetime, timedelta, timezone

            user_repo = SqlUserRepository(db)
            consent_repo = SqlDataConsentRepository(db)
            membership_repo = SqlGroupMembershipRepository(db)
            processing_record_repo = SqlDataProcessingRecordRepository(db)
            refresh_token_repo = SqlRefreshTokenRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            # Create user and refresh token
            user_id = uuid4()
            user = User(
                id=user_id, name="Token", email="token@test.com", password_hash="hashed"
            )
            user_repo.save(user)

            token = RefreshToken(
                user_id=user_id,
                token_hash="abc123hash",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                revoked=False,
            )
            refresh_token_repo.save(token)
            db.commit()

            # Execute delete
            use_case = DeleteUserAccount(
                user_repository=user_repo,
                refresh_token_repository=refresh_token_repo,
                membership_repository=membership_repo,
                consent_repository=consent_repo,
                processing_record_repository=processing_record_repo,
                audit_service=audit_service,
            )
            use_case.execute(user_id)
            db.commit()

            # Verify token is revoked
            active_tokens = refresh_token_repo.find_active_by_user_id(user_id)
            assert active_tokens == []
        finally:
            db.close()

    def test_audit_log_created_with_account_deleted(self):
        """Delete creates an audit log entry with ACCOUNT_DELETED action."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            consent_repo = SqlDataConsentRepository(db)
            membership_repo = SqlGroupMembershipRepository(db)
            processing_record_repo = SqlDataProcessingRecordRepository(db)
            refresh_token_repo = SqlRefreshTokenRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            # Create user
            user_id = uuid4()
            user = User(
                id=user_id, name="Audit", email="auditdel@test.com", password_hash="hashed"
            )
            user_repo.save(user)
            db.commit()

            # Execute delete
            use_case = DeleteUserAccount(
                user_repository=user_repo,
                refresh_token_repository=refresh_token_repo,
                membership_repository=membership_repo,
                consent_repository=consent_repo,
                processing_record_repository=processing_record_repo,
                audit_service=audit_service,
            )
            use_case.execute(user_id)
            db.commit()

            # Check audit log
            logs = audit_repo.find_by_actor(user_id)
            assert len(logs) == 1
            assert logs[0].action == AuditAction.ACCOUNT_DELETED
            assert f"user:{user_id}:deleted" in logs[0].affected_entity
        finally:
            db.close()

    def test_user_not_found_raises_error(self):
        """Delete raises UserNotFoundError for non-existent user."""
        db = self._get_session()
        try:
            user_repo = SqlUserRepository(db)
            consent_repo = SqlDataConsentRepository(db)
            membership_repo = SqlGroupMembershipRepository(db)
            processing_record_repo = SqlDataProcessingRecordRepository(db)
            refresh_token_repo = SqlRefreshTokenRepository(db)
            audit_repo = SqlAuditLogRepository(db)
            audit_service = AuditService(repository=audit_repo)

            use_case = DeleteUserAccount(
                user_repository=user_repo,
                refresh_token_repository=refresh_token_repo,
                membership_repository=membership_repo,
                consent_repository=consent_repo,
                processing_record_repository=processing_record_repo,
                audit_service=audit_service,
            )

            with pytest.raises(DeleteUserNotFoundError):
                use_case.execute(uuid4())
        finally:
            db.close()


# --- Integration tests for endpoints ---


class TestExportEndpoint:
    """GET /users/me/export — integration tests."""

    def test_returns_structured_data(self):
        """Export returns all user data in structured JSON format."""
        user_id, token = _register_and_login()

        response = client.get(
            "/users/me/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["user"]["name"] == "Test User"
        assert data["user"]["email"] == "test@example.com"
        assert "created_at" in data["user"]
        assert isinstance(data["consents"], list)
        assert isinstance(data["memberships"], list)
        assert isinstance(data["processing_records"], list)

    def test_does_not_include_password_hash(self):
        """Export never includes password_hash."""
        _, token = _register_and_login()

        response = client.get(
            "/users/me/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()

        assert "password_hash" not in data["user"]
        assert "password" not in data["user"]

    def test_requires_auth(self):
        """Export requires a valid Authorization header."""
        response = client.get("/users/me/export")
        assert response.status_code == 422  # Missing header

    def test_rejects_invalid_token(self):
        """Export rejects invalid bearer token."""
        response = client.get(
            "/users/me/export",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401


class TestGetOppositionsEndpoint:
    """GET /users/me/oppositions — integration tests.

    Requirements: 2.3, 3.1, 3.4
    """

    def test_returns_empty_list_for_new_user(self):
        """New user with no oppositions gets 200 with an empty list."""
        _, token = _register_and_login(
            email="oppositions_empty@test.com", name="Empty Oppositions"
        )

        response = client.get(
            "/users/me/oppositions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {"opposed_purposes": []}

    def test_returns_list_after_post(self):
        """After POST /users/me/oppose, GET returns a list containing that purpose."""
        _, token = _register_and_login(
            email="oppositions_after_post@test.com", name="Post Oppositions"
        )

        # Register an opposition
        post_response = client.post(
            "/users/me/oppose",
            json={"purpose": "Estadísticas de uso"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert post_response.status_code == 200

        # Retrieve oppositions
        response = client.get(
            "/users/me/oppositions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Estadísticas de uso" in data["opposed_purposes"]

    def test_no_duplicates_after_double_post(self):
        """Registering the same purpose twice results in exactly one occurrence."""
        _, token = _register_and_login(
            email="oppositions_dedup@test.com", name="Dedup Oppositions"
        )

        purpose = "Personalización de contenido"

        # Register the same opposition twice
        for _ in range(2):
            post_response = client.post(
                "/users/me/oppose",
                json={"purpose": purpose},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert post_response.status_code == 200

        # Retrieve oppositions — must contain exactly one occurrence
        response = client.get(
            "/users/me/oppositions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        purposes = response.json()["opposed_purposes"]
        assert purposes.count(purpose) == 1

    def test_requires_auth(self):
        """GET /users/me/oppositions without Authorization header returns 422."""
        response = client.get("/users/me/oppositions")
        assert response.status_code == 422

    def test_rejects_invalid_token(self):
        """GET /users/me/oppositions with an invalid token returns 401."""
        response = client.get(
            "/users/me/oppositions",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_post_still_works_after_fix(self):
        """Regression guard: POST /users/me/oppose returns OpposeResponse with opposed=True."""
        _, token = _register_and_login(
            email="oppositions_regression@test.com", name="Regression Guard"
        )

        response = client.post(
            "/users/me/oppose",
            json={"purpose": "Recomendaciones de lectura"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["opposed"] is True
        assert data["processing_purpose"] == "Recomendaciones de lectura"


class TestDeleteEndpoint:
    """DELETE /users/me — integration tests."""

    def test_deletes_account(self):
        """Delete account returns confirmation and subsequent login fails."""
        _, token = _register_and_login(email="deleteme@test.com")

        # Delete account
        response = client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["detail"] == "account_deleted"

        # Try to login — should fail (user doesn't exist)
        login_response = client.post(
            "/auth/login",
            json={"email": "deleteme@test.com", "password": "SecurePass123!"},
        )
        assert login_response.status_code == 401

    def test_requires_auth(self):
        """Delete requires a valid Authorization header."""
        response = client.delete("/users/me")
        assert response.status_code == 422  # Missing header

    def test_rejects_invalid_token(self):
        """Delete rejects invalid bearer token."""
        response = client.delete(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
