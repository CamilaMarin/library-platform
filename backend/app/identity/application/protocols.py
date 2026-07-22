"""Repository interfaces for the Identity & Privacy bounded context.

These protocols define the contract between application and infrastructure layers.
Implementations live in identity/infrastructure/. Domain never imports these directly.

Reference: ADR-0017 (cloud agnostic — all dependencies behind abstractions)
"""

from typing import Protocol
from uuid import UUID

from app.identity.domain.entities import (
    AuditLog,
    DataConsent,
    DataProcessingRecord,
    RetentionPolicy,
)


class DataConsentRepository(Protocol):
    """Persistence interface for DataConsent."""

    def save(self, consent: DataConsent) -> DataConsent: ...

    def find_by_user_id(self, user_id: UUID) -> DataConsent | None: ...


class DataProcessingRecordRepository(Protocol):
    """Persistence interface for DataProcessingRecord."""

    def save(self, record: DataProcessingRecord) -> DataProcessingRecord: ...

    def find_by_user_id(self, user_id: UUID) -> list[DataProcessingRecord]: ...


class AuditLogRepository(Protocol):
    """Persistence interface for AuditLog."""

    def save(self, entry: AuditLog) -> AuditLog: ...

    def find_by_actor(self, actor_user_id: UUID) -> list[AuditLog]: ...


class RetentionPolicyRepository(Protocol):
    """Persistence interface for RetentionPolicy."""

    def find_active(self) -> list[RetentionPolicy]: ...

    def find_by_data_type(self, data_type: str) -> RetentionPolicy | None: ...
