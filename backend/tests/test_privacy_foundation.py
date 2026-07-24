"""Tests for M0 Privacy Foundation.

Domain unit tests: entity invariants, AuditLog service behavior.
No database required — uses in-memory test doubles.

Reference: privacy/tasks.md#1, #2
"""

from uuid import uuid4

import pytest

from app.identity.application.audit_service import AuditService
from app.identity.domain.entities import (
    AuditAction,
    AuditLog,
    DataConsent,
    DataProcessingRecord,
    RetentionPolicy,
)

# --- Domain entity tests ---


class TestDataConsent:
    def test_valid_consent_creation(self):
        consent = DataConsent(policy_version="1.0", purpose="account_creation")
        assert consent.policy_version == "1.0"
        assert consent.purpose == "account_creation"
        assert consent.id is not None

    def test_consent_requires_policy_version(self):
        with pytest.raises(ValueError, match="policy_version"):
            DataConsent(policy_version="", purpose="account_creation")

    def test_consent_requires_purpose(self):
        with pytest.raises(ValueError, match="purpose"):
            DataConsent(policy_version="1.0", purpose="")


class TestDataProcessingRecord:
    def test_valid_record_creation(self):
        user_id = uuid4()
        record = DataProcessingRecord(
            user_id=user_id,
            data_type="email",
            purpose="authentication",
            legal_basis="consent",
        )
        assert record.user_id == user_id
        assert record.data_type == "email"
        assert record.retention_expires_at is None


class TestAuditLog:
    def test_valid_audit_entry(self):
        user_id = uuid4()
        entry = AuditLog(
            actor_user_id=user_id,
            action=AuditAction.USER_REGISTERED,
            affected_entity="user:123",
        )
        assert entry.actor_user_id == user_id
        assert entry.action == AuditAction.USER_REGISTERED

    def test_audit_allows_null_actor(self):
        entry = AuditLog(
            actor_user_id=None,
            action=AuditAction.ARCO_REQUEST,
            affected_entity="system",
        )
        assert entry.actor_user_id is None


class TestRetentionPolicy:
    def test_default_duration(self):
        policy = RetentionPolicy(data_type="user_profile")
        assert policy.duration_days == 365
        assert policy.active is True

    def test_custom_duration(self):
        policy = RetentionPolicy(data_type="audit_logs", duration_days=730)
        assert policy.duration_days == 730


# --- AuditService tests ---


class InMemoryAuditLogRepository:
    """Test double for AuditLogRepository."""

    def __init__(self):
        self.entries: list[AuditLog] = []

    def save(self, entry: AuditLog) -> AuditLog:
        self.entries.append(entry)
        return entry

    def find_by_actor(self, actor_user_id):
        return [e for e in self.entries if e.actor_user_id == actor_user_id]


class TestAuditService:
    def test_log_creates_entry(self):
        repo = InMemoryAuditLogRepository()
        service = AuditService(repository=repo)
        user_id = uuid4()

        entry = service.log(
            actor_user_id=user_id,
            action=AuditAction.USER_REGISTERED,
            affected_entity=f"user:{user_id}",
        )

        assert entry.actor_user_id == user_id
        assert entry.action == AuditAction.USER_REGISTERED
        assert len(repo.entries) == 1

    def test_log_multiple_entries(self):
        repo = InMemoryAuditLogRepository()
        service = AuditService(repository=repo)
        user_id = uuid4()

        service.log(user_id, AuditAction.USER_LOGIN, f"user:{user_id}")
        service.log(user_id, AuditAction.FILE_UPLOADED, "copy:abc")

        assert len(repo.entries) == 2
        assert repo.entries[0].action == AuditAction.USER_LOGIN
        assert repo.entries[1].action == AuditAction.FILE_UPLOADED
