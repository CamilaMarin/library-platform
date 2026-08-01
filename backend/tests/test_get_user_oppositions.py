"""Unit tests for GetUserOppositions use case.

Tests the GetUserOppositions use case with real SQL repositories (no mocks),
following the pattern of TestExportUserDataUseCase in test_arco_integration.py.

Reference: view-registered-oppositions/requirements.md Req 2.3
"""

from uuid import uuid4

import pytest

from app.identity.application.audit_service import AuditService
from app.identity.application.get_user_oppositions import (
    GetUserOppositions,
    UserNotFoundError,
)
from app.identity.domain.entities import AuditAction, User
from app.identity.infrastructure.repositories import (
    SqlAuditLogRepository,
    SqlUserRepository,
)
from tests.conftest import TestSession


class TestGetUserOppositions:
    """Unit tests for GetUserOppositions use case using real SQL repos."""

    def _get_session(self):
        return TestSession()

    def _make_use_case(self, db):
        """Instantiate the use case with real SQL repos bound to the given session."""
        user_repo = SqlUserRepository(db)
        audit_repo = SqlAuditLogRepository(db)
        audit_service = AuditService(repository=audit_repo)
        return (
            GetUserOppositions(user_repository=user_repo, audit_service=audit_service),
            user_repo,
            audit_repo,
        )

    def test_returns_empty_list_for_user_without_oppositions(self):
        """Fresh user with empty privacy_settings → execute() returns []."""
        db = self._get_session()
        try:
            use_case, user_repo, _ = self._make_use_case(db)

            user_id = uuid4()
            user = User(
                id=user_id,
                name="Sin Oposiciones",
                email="sin_oposiciones@test.com",
                password_hash="hashed",
                privacy_settings={},
            )
            user_repo.save(user)
            db.commit()

            result = use_case.execute(user_id)
            db.commit()

            assert result == []
        finally:
            db.close()

    def test_returns_correct_list(self):
        """User with opposed_purposes ["A", "B"] in privacy_settings → returns ["A", "B"]."""
        db = self._get_session()
        try:
            use_case, user_repo, _ = self._make_use_case(db)

            user_id = uuid4()
            user = User(
                id=user_id,
                name="Con Oposiciones",
                email="con_oposiciones@test.com",
                password_hash="hashed",
                privacy_settings={"opposed_purposes": ["A", "B"]},
            )
            user_repo.save(user)
            db.commit()

            result = use_case.execute(user_id)
            db.commit()

            assert result == ["A", "B"]
        finally:
            db.close()

    def test_user_not_found_raises_error(self):
        """Non-existent user_id → raises UserNotFoundError."""
        db = self._get_session()
        try:
            use_case, _, _ = self._make_use_case(db)

            with pytest.raises(UserNotFoundError):
                use_case.execute(uuid4())
        finally:
            db.close()

    def test_audit_log_created_with_arco_request(self):
        """execute() writes an audit log with ARCO_REQUEST and the correct affected_entity."""
        db = self._get_session()
        try:
            use_case, user_repo, audit_repo = self._make_use_case(db)

            user_id = uuid4()
            user = User(
                id=user_id,
                name="Audit Test",
                email="audit_oppositions@test.com",
                password_hash="hashed",
                privacy_settings={"opposed_purposes": ["Perfilado"]},
            )
            user_repo.save(user)
            db.commit()

            use_case.execute(user_id)
            db.commit()

            logs = audit_repo.find_by_actor(user_id)
            assert len(logs) == 1
            assert logs[0].action == AuditAction.ARCO_REQUEST
            assert f"user:{user_id}:oppositions" in logs[0].affected_entity
        finally:
            db.close()

    def test_null_privacy_settings(self):
        """User with privacy_settings effectively empty/null → execute() returns [].

        The UserModel column is nullable=False so actual NULL cannot be stored in
        production PostgreSQL. The SqlUserRepository.find_by_id() normalises
        None → {} via `or {}`. The use case adds a second guard with
        `(user.privacy_settings or {})` to be defensive against any legacy path
        that might surface a Python-level None. This test verifies that a user
        without the 'opposed_purposes' key (equivalent to the null/empty scenario)
        returns an empty list without raising an exception.
        """
        db = self._get_session()
        try:
            use_case, user_repo, _ = self._make_use_case(db)

            # A user whose privacy_settings has no 'opposed_purposes' key mirrors
            # the legacy null scenario: the use case must return [] defensively.
            user_id = uuid4()
            user = User(
                id=user_id,
                name="Legacy User",
                email="legacy_null@test.com",
                password_hash="hashed",
                privacy_settings={"other_setting": "value"},  # no opposed_purposes key
            )
            user_repo.save(user)
            db.commit()

            result = use_case.execute(user_id)
            db.commit()

            assert result == []
        finally:
            db.close()
