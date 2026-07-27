"""Tests for the RetentionJob service.

Validates:
- Expired processing records are deleted
- Old audit logs are anonymized per policy
- Policies with active=False are skipped
- Duration comes from DB, not hardcoded (ADR-0016)
- Expired consents are removed
- Inactive accounts are flagged (not auto-deleted)

Reference: privacy/requirements.md Req 1.7, ADR-0016
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.identity.application.audit_service import AuditService
from app.identity.application.retention_job import (
    DELETED_USER_SENTINEL,
    RetentionJob,
)
from app.identity.domain.entities import AuditAction
from app.identity.infrastructure.models import (
    AuditLogModel,
    DataConsentModel,
    DataProcessingRecordModel,
    RetentionPolicyModel,
    UserModel,
)
from app.identity.infrastructure.repositories import SqlAuditLogRepository
from tests.conftest import TestSession


@pytest.fixture
def db_session():
    """Provide a database session for tests."""
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def audit_service(db_session: Session) -> AuditService:
    """Provide an AuditService backed by the test session."""
    repo = SqlAuditLogRepository(db_session)
    return AuditService(repository=repo)


def _create_retention_policy(
    session: Session,
    data_type: str,
    duration_days: int,
    active: bool = True,
) -> RetentionPolicyModel:
    """Helper to insert a retention policy."""
    policy = RetentionPolicyModel(
        id=uuid.uuid4(),
        data_type=data_type,
        duration_days=duration_days,
        description=f"Test policy for {data_type}",
        active=active,
    )
    session.add(policy)
    session.flush()
    return policy


class TestProcessingRecordsRetention:
    """Test that expired processing records are deleted."""

    def test_expired_records_are_deleted(self, db_session: Session, audit_service: AuditService):
        """Processing records past their retention_expires_at are removed."""
        _create_retention_policy(db_session, "processing_records", duration_days=90)

        user_id = uuid.uuid4()
        # Expired record (retention expired yesterday)
        expired_record = DataProcessingRecordModel(
            id=uuid.uuid4(),
            user_id=user_id,
            data_type="personal_data",
            purpose="service",
            legal_basis="consent",
            collected_at=datetime.now(timezone.utc) - timedelta(days=100),
            retention_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        # Active record (retention expires in the future)
        active_record = DataProcessingRecordModel(
            id=uuid.uuid4(),
            user_id=user_id,
            data_type="personal_data",
            purpose="service",
            legal_basis="consent",
            collected_at=datetime.now(timezone.utc) - timedelta(days=50),
            retention_expires_at=datetime.now(timezone.utc) + timedelta(days=40),
        )
        db_session.add_all([expired_record, active_record])
        db_session.flush()

        job = RetentionJob(session=db_session, audit_service=audit_service)
        result = job.execute()

        assert result.records_affected >= 1

        # Expired record should be deleted
        remaining = (
            db_session.query(DataProcessingRecordModel)
            .filter(DataProcessingRecordModel.user_id == user_id)
            .all()
        )
        remaining_ids = [r.id for r in remaining]
        assert expired_record.id not in remaining_ids
        assert active_record.id in remaining_ids

    def test_records_without_expiration_are_not_deleted(
        self, db_session: Session, audit_service: AuditService
    ):
        """Processing records with no retention_expires_at are not touched."""
        _create_retention_policy(db_session, "processing_records", duration_days=90)

        record = DataProcessingRecordModel(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data_type="personal_data",
            purpose="service",
            legal_basis="consent",
            collected_at=datetime.now(timezone.utc) - timedelta(days=200),
            retention_expires_at=None,
        )
        db_session.add(record)
        db_session.flush()

        job = RetentionJob(session=db_session, audit_service=audit_service)
        job.execute()

        remaining = db_session.query(DataProcessingRecordModel).filter(
            DataProcessingRecordModel.id == record.id
        ).first()
        assert remaining is not None


class TestAuditLogRetention:
    """Test that old audit logs are anonymized per policy."""

    def test_old_audit_logs_are_anonymized(self, db_session: Session, audit_service: AuditService):
        """Audit logs older than duration_days have actor_user_id replaced with sentinel."""
        _create_retention_policy(db_session, "audit_logs", duration_days=30)

        user_id = uuid.uuid4()
        # Old log (beyond retention)
        old_log = AuditLogModel(
            id=uuid.uuid4(),
            actor_user_id=user_id,
            action=AuditAction.USER_LOGIN.value,
            affected_entity="user:login",
            timestamp=datetime.now(timezone.utc) - timedelta(days=60),
        )
        # Recent log (within retention)
        recent_log = AuditLogModel(
            id=uuid.uuid4(),
            actor_user_id=user_id,
            action=AuditAction.USER_LOGIN.value,
            affected_entity="user:login",
            timestamp=datetime.now(timezone.utc) - timedelta(days=5),
        )
        db_session.add_all([old_log, recent_log])
        db_session.flush()

        job = RetentionJob(session=db_session, audit_service=audit_service)
        result = job.execute()

        assert result.records_affected >= 1

        # Old log should be anonymized
        db_session.refresh(old_log)
        assert old_log.actor_user_id == DELETED_USER_SENTINEL

        # Recent log should keep its original actor
        db_session.refresh(recent_log)
        assert recent_log.actor_user_id == user_id

    def test_already_anonymized_logs_are_not_counted(
        self, db_session: Session, audit_service: AuditService
    ):
        """Logs already anonymized with sentinel are not reprocessed."""
        _create_retention_policy(db_session, "audit_logs", duration_days=30)

        already_anon = AuditLogModel(
            id=uuid.uuid4(),
            actor_user_id=DELETED_USER_SENTINEL,
            action=AuditAction.ACCOUNT_DELETED.value,
            affected_entity="user:purged",
            timestamp=datetime.now(timezone.utc) - timedelta(days=60),
        )
        db_session.add(already_anon)
        db_session.flush()

        job = RetentionJob(session=db_session, audit_service=audit_service)
        result = job.execute()

        # The already-anonymized log should not be counted as affected
        audit_details = [d for d in result.details if "audit_logs" in d]
        assert any("no records to process" in d for d in audit_details)


class TestInactivePoliciesSkipped:
    """Test that policies with active=False are skipped."""

    def test_inactive_policy_is_not_executed(
        self, db_session: Session, audit_service: AuditService
    ):
        """Policies marked as inactive should be completely ignored."""
        _create_retention_policy(
            db_session, "processing_records", duration_days=1, active=False
        )

        # Create an expired record that WOULD be deleted if policy were active
        record = DataProcessingRecordModel(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data_type="personal_data",
            purpose="service",
            legal_basis="consent",
            collected_at=datetime.now(timezone.utc) - timedelta(days=200),
            retention_expires_at=datetime.now(timezone.utc) - timedelta(days=100),
        )
        db_session.add(record)
        db_session.flush()

        job = RetentionJob(session=db_session, audit_service=audit_service)
        result = job.execute()

        # No policies should be processed
        assert result.policies_processed == 0
        assert result.records_affected == 0

        # Record should still exist
        remaining = db_session.query(DataProcessingRecordModel).filter(
            DataProcessingRecordModel.id == record.id
        ).first()
        assert remaining is not None


class TestDurationFromDatabase:
    """Test that duration comes from DB, not hardcoded (ADR-0016)."""

    def test_changing_duration_affects_behavior(
        self, db_session: Session, audit_service: AuditService
    ):
        """Different duration_days values in the DB produce different results.

        This proves the retention job reads duration from the database at runtime.
        """
        user_id = uuid.uuid4()

        # Create an audit log that is 45 days old
        log_entry = AuditLogModel(
            id=uuid.uuid4(),
            actor_user_id=user_id,
            action=AuditAction.USER_LOGIN.value,
            affected_entity="user:login",
            timestamp=datetime.now(timezone.utc) - timedelta(days=45),
        )
        db_session.add(log_entry)
        db_session.flush()

        # First run: 60-day retention - log should NOT be anonymized
        policy = _create_retention_policy(db_session, "audit_logs", duration_days=60)

        job = RetentionJob(session=db_session, audit_service=audit_service)
        job.execute()

        db_session.refresh(log_entry)
        assert log_entry.actor_user_id == user_id  # Not anonymized

        # Update policy to 30 days - now the 45-day-old log SHOULD be anonymized
        db_session.query(RetentionPolicyModel).filter(
            RetentionPolicyModel.id == policy.id
        ).update({"duration_days": 30})
        db_session.flush()

        job2 = RetentionJob(session=db_session, audit_service=audit_service)
        job2.execute()

        db_session.refresh(log_entry)
        assert log_entry.actor_user_id == DELETED_USER_SENTINEL  # Now anonymized

    def test_no_hardcoded_constants_used(
        self, db_session: Session, audit_service: AuditService
    ):
        """With no active policies in the DB, the job does nothing - proving
        it doesn't fall back to any hardcoded defaults."""
        # No policies inserted at all
        job = RetentionJob(session=db_session, audit_service=audit_service)
        result = job.execute()

        assert result.policies_processed == 0
        assert result.records_affected == 0


class TestExpiredConsentsRetention:
    """Test that expired consent records are removed."""

    def test_old_consents_are_deleted(self, db_session: Session, audit_service: AuditService):
        """Consent records older than duration_days are removed."""
        _create_retention_policy(db_session, "expired_consents", duration_days=90)

        user_id = uuid.uuid4()
        # Old consent
        old_consent = DataConsentModel(
            id=uuid.uuid4(),
            user_id=user_id,
            timestamp=datetime.now(timezone.utc) - timedelta(days=120),
            policy_version="v1",
            purpose="data_processing",
        )
        # Recent consent
        recent_consent = DataConsentModel(
            id=uuid.uuid4(),
            user_id=user_id,
            timestamp=datetime.now(timezone.utc) - timedelta(days=10),
            policy_version="v2",
            purpose="data_processing",
        )
        db_session.add_all([old_consent, recent_consent])
        db_session.flush()

        job = RetentionJob(session=db_session, audit_service=audit_service)
        result = job.execute()

        assert result.records_affected >= 1

        remaining = (
            db_session.query(DataConsentModel)
            .filter(DataConsentModel.user_id == user_id)
            .all()
        )
        remaining_ids = [r.id for r in remaining]
        assert old_consent.id not in remaining_ids
        assert recent_consent.id in remaining_ids


class TestInactiveAccountsRetention:
    """Test that inactive accounts are flagged, not auto-deleted."""

    def test_inactive_account_is_flagged(self, db_session: Session, audit_service: AuditService):
        """Accounts with no login in duration_days are flagged for deletion."""
        _create_retention_policy(db_session, "inactive_accounts", duration_days=90)

        # Create a user who hasn't logged in for 120 days
        user = UserModel(
            id=uuid.uuid4(),
            name="Inactive User",
            email="inactive@example.com",
            password_hash="hash123",
            privacy_settings={},
            created_at=datetime.now(timezone.utc) - timedelta(days=200),
        )
        db_session.add(user)
        db_session.flush()

        job = RetentionJob(session=db_session, audit_service=audit_service)
        result = job.execute()

        assert result.records_affected >= 1

        db_session.refresh(user)
        assert user.privacy_settings.get("flagged_for_deletion") is True

    def test_active_account_is_not_flagged(
        self, db_session: Session, audit_service: AuditService
    ):
        """Accounts with recent login are not flagged."""
        _create_retention_policy(db_session, "inactive_accounts", duration_days=90)

        user = UserModel(
            id=uuid.uuid4(),
            name="Active User",
            email="active@example.com",
            password_hash="hash123",
            privacy_settings={},
            created_at=datetime.now(timezone.utc) - timedelta(days=200),
        )
        db_session.add(user)
        db_session.flush()

        # Simulate a recent login via audit log
        login_log = AuditLogModel(
            id=uuid.uuid4(),
            actor_user_id=user.id,
            action=AuditAction.USER_LOGIN.value,
            affected_entity="user:login",
            timestamp=datetime.now(timezone.utc) - timedelta(days=5),
        )
        db_session.add(login_log)
        db_session.flush()

        job = RetentionJob(session=db_session, audit_service=audit_service)
        job.execute()

        db_session.refresh(user)
        assert user.privacy_settings.get("flagged_for_deletion") is not True


class TestRetentionJobResult:
    """Test the result reporting of the retention job."""

    def test_result_contains_details_per_policy(
        self, db_session: Session, audit_service: AuditService
    ):
        """Each processed policy produces a detail entry in the result."""
        _create_retention_policy(db_session, "audit_logs", duration_days=30)
        _create_retention_policy(db_session, "expired_consents", duration_days=60)

        job = RetentionJob(session=db_session, audit_service=audit_service)
        result = job.execute()

        assert result.policies_processed == 2
        assert len(result.details) == 2
