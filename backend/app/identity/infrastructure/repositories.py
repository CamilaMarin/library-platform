"""Repository implementations for the privacy foundation.

These implement the protocols defined in application/protocols.py.
Reference: ADR-0017 (infrastructure implements abstractions)
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.identity.domain.entities import (
    AuditAction,
    AuditLog,
    DataConsent,
    DataProcessingRecord,
    RetentionPolicy,
)
from app.identity.infrastructure.models import (
    AuditLogModel,
    DataConsentModel,
    DataProcessingRecordModel,
    RetentionPolicyModel,
)


class SqlDataConsentRepository:
    """SQLAlchemy implementation of DataConsentRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, consent: DataConsent) -> DataConsent:
        model = DataConsentModel(
            id=consent.id,
            user_id=consent.user_id,
            timestamp=consent.timestamp,
            policy_version=consent.policy_version,
            purpose=consent.purpose,
        )
        self._session.add(model)
        self._session.flush()
        return consent

    def find_by_user_id(self, user_id: UUID) -> DataConsent | None:
        model = (
            self._session.query(DataConsentModel)
            .filter(DataConsentModel.user_id == user_id)
            .first()
        )
        if not model:
            return None
        return DataConsent(
            id=model.id,
            user_id=model.user_id,
            timestamp=model.timestamp,
            policy_version=model.policy_version,
            purpose=model.purpose,
        )


class SqlDataProcessingRecordRepository:
    """SQLAlchemy implementation of DataProcessingRecordRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, record: DataProcessingRecord) -> DataProcessingRecord:
        model = DataProcessingRecordModel(
            id=record.id,
            user_id=record.user_id,
            data_type=record.data_type,
            purpose=record.purpose,
            legal_basis=record.legal_basis,
            collected_at=record.collected_at,
            retention_expires_at=record.retention_expires_at,
        )
        self._session.add(model)
        self._session.flush()
        return record

    def find_by_user_id(self, user_id: UUID) -> list[DataProcessingRecord]:
        models = (
            self._session.query(DataProcessingRecordModel)
            .filter(DataProcessingRecordModel.user_id == user_id)
            .all()
        )
        return [
            DataProcessingRecord(
                id=m.id,
                user_id=m.user_id,
                data_type=m.data_type,
                purpose=m.purpose,
                legal_basis=m.legal_basis,
                collected_at=m.collected_at,
                retention_expires_at=m.retention_expires_at,
            )
            for m in models
        ]


class SqlAuditLogRepository:
    """SQLAlchemy implementation of AuditLogRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, entry: AuditLog) -> AuditLog:
        model = AuditLogModel(
            id=entry.id,
            actor_user_id=entry.actor_user_id,
            action=entry.action.value,
            affected_entity=entry.affected_entity,
            timestamp=entry.timestamp,
        )
        self._session.add(model)
        self._session.flush()
        return entry

    def find_by_actor(self, actor_user_id: UUID) -> list[AuditLog]:
        models = (
            self._session.query(AuditLogModel)
            .filter(AuditLogModel.actor_user_id == actor_user_id)
            .order_by(AuditLogModel.timestamp.desc())
            .all()
        )
        return [
            AuditLog(
                id=m.id,
                actor_user_id=m.actor_user_id,
                action=AuditAction(m.action),
                affected_entity=m.affected_entity,
                timestamp=m.timestamp,
            )
            for m in models
        ]


class SqlRetentionPolicyRepository:
    """SQLAlchemy implementation of RetentionPolicyRepository."""

    def __init__(self, session: Session):
        self._session = session

    def find_active(self) -> list[RetentionPolicy]:
        models = (
            self._session.query(RetentionPolicyModel)
            .filter(RetentionPolicyModel.active.is_(True))
            .all()
        )
        return [
            RetentionPolicy(
                id=m.id,
                data_type=m.data_type,
                duration_days=m.duration_days,
                description=m.description,
                active=m.active,
            )
            for m in models
        ]

    def find_by_data_type(self, data_type: str) -> RetentionPolicy | None:
        model = (
            self._session.query(RetentionPolicyModel)
            .filter(RetentionPolicyModel.data_type == data_type)
            .first()
        )
        if not model:
            return None
        return RetentionPolicy(
            id=model.id,
            data_type=model.data_type,
            duration_days=model.duration_days,
            description=model.description,
            active=model.active,
        )
