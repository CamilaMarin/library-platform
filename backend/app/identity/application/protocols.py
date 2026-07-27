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
    FamilyGroup,
    GroupMembership,
    MembershipStatus,
    RefreshToken,
    RetentionPolicy,
    User,
)


class DataConsentRepository(Protocol):
    """Persistence interface for DataConsent."""

    def save(self, consent: DataConsent) -> DataConsent: ...

    def find_by_user_id(self, user_id: UUID) -> DataConsent | None: ...

    def find_all_by_user_id(self, user_id: UUID) -> list[DataConsent]: ...

    def delete_by_user_id(self, user_id: UUID) -> None: ...


class DataProcessingRecordRepository(Protocol):
    """Persistence interface for DataProcessingRecord."""

    def save(self, record: DataProcessingRecord) -> DataProcessingRecord: ...

    def find_by_user_id(self, user_id: UUID) -> list[DataProcessingRecord]: ...

    def delete_by_user_id(self, user_id: UUID) -> None: ...


class AuditLogRepository(Protocol):
    """Persistence interface for AuditLog."""

    def save(self, entry: AuditLog) -> AuditLog: ...

    def find_by_actor(self, actor_user_id: UUID) -> list[AuditLog]: ...


class RetentionPolicyRepository(Protocol):
    """Persistence interface for RetentionPolicy."""

    def find_active(self) -> list[RetentionPolicy]: ...

    def find_by_data_type(self, data_type: str) -> RetentionPolicy | None: ...


class UserRepository(Protocol):
    """Persistence interface for User."""

    def save(self, user: User) -> User: ...

    def find_by_email(self, email: str) -> User | None: ...

    def find_by_id(self, user_id: UUID) -> User | None: ...

    def update(self, user: User) -> User: ...

    def delete(self, user_id: UUID) -> None: ...


class RefreshTokenRepository(Protocol):
    """Persistence interface for RefreshToken."""

    def save(self, token: RefreshToken) -> RefreshToken: ...

    def find_by_token_hash(self, token_hash: str) -> RefreshToken | None: ...

    def find_active_by_user_id(self, user_id: UUID) -> list[RefreshToken]: ...

    def revoke(self, token_id: UUID) -> None: ...

    def revoke_all_by_user_id(self, user_id: UUID) -> None: ...


class FamilyGroupRepository(Protocol):
    """Persistence interface for FamilyGroup."""

    def save(self, group: FamilyGroup) -> FamilyGroup: ...

    def find_by_id(self, group_id: UUID) -> FamilyGroup | None: ...


class GroupMembershipRepository(Protocol):
    """Persistence interface for GroupMembership."""

    def save(self, membership: GroupMembership) -> GroupMembership: ...

    def find_by_id(self, membership_id: UUID) -> GroupMembership | None: ...

    def find_by_group_id(self, group_id: UUID) -> list[GroupMembership]: ...

    def find_by_user_id(self, user_id: UUID) -> list[GroupMembership]: ...

    def find_by_user_and_group(self, user_id: UUID, group_id: UUID) -> GroupMembership | None: ...

    def update_status(self, membership_id: UUID, status: MembershipStatus) -> None: ...

    def delete_by_user_id(self, user_id: UUID) -> None: ...
