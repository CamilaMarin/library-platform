"""ExportUserData use case — exports all identity-owned personal data for a user.

Integrates with the Privacy module's ARCO (access) right.
The export NEVER includes password_hash.

Reference: authentication/requirements.md Req 4.1, 4.2
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.identity.application.audit_service import AuditService
from app.identity.application.protocols import (
    DataConsentRepository,
    DataProcessingRecordRepository,
    GroupMembershipRepository,
    UserRepository,
)
from app.identity.domain.entities import AuditAction


class UserNotFoundError(Exception):
    """Raised when the user does not exist."""

    pass


@dataclass
class ExportedConsent:
    """Exported consent record."""

    id: UUID
    timestamp: datetime
    policy_version: str
    purpose: str


@dataclass
class ExportedMembership:
    """Exported group membership record."""

    id: UUID
    group_id: UUID
    status: str
    created_at: datetime


@dataclass
class ExportedProcessingRecord:
    """Exported data processing record."""

    id: UUID
    data_type: str
    purpose: str
    legal_basis: str
    collected_at: datetime
    retention_expires_at: datetime | None


@dataclass
class ExportedUser:
    """Exported user profile (no password_hash)."""

    name: str
    email: str
    privacy_settings: dict
    created_at: datetime


@dataclass
class ExportResult:
    """Structured export of all identity-owned data for a user."""

    user: ExportedUser
    consents: list[ExportedConsent]
    memberships: list[ExportedMembership]
    processing_records: list[ExportedProcessingRecord]


class ExportUserData:
    """Use case: export all identity-owned personal data for a user (ARCO access right)."""

    def __init__(
        self,
        user_repository: UserRepository,
        consent_repository: DataConsentRepository,
        membership_repository: GroupMembershipRepository,
        processing_record_repository: DataProcessingRecordRepository,
        audit_service: AuditService,
    ):
        self._user_repo = user_repository
        self._consent_repo = consent_repository
        self._membership_repo = membership_repository
        self._processing_record_repo = processing_record_repository
        self._audit_service = audit_service

    def execute(self, user_id: UUID) -> ExportResult:
        """Export all identity-owned data for the given user.

        Raises UserNotFoundError if user does not exist.
        """
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")

        # Collect all identity-owned data
        consents = self._consent_repo.find_all_by_user_id(user_id)
        memberships = self._membership_repo.find_by_user_id(user_id)
        processing_records = self._processing_record_repo.find_by_user_id(user_id)

        # Log ARCO request
        self._audit_service.log(
            actor_user_id=user_id,
            action=AuditAction.ARCO_REQUEST,
            affected_entity=f"user:{user_id}:export",
        )

        return ExportResult(
            user=ExportedUser(
                name=user.name,
                email=user.email,
                privacy_settings=user.privacy_settings,
                created_at=user.created_at,
            ),
            consents=[
                ExportedConsent(
                    id=c.id,
                    timestamp=c.timestamp,
                    policy_version=c.policy_version,
                    purpose=c.purpose,
                )
                for c in consents
            ],
            memberships=[
                ExportedMembership(
                    id=m.id,
                    group_id=m.group_id,
                    status=m.status.value if hasattr(m.status, "value") else m.status,
                    created_at=m.created_at,
                )
                for m in memberships
            ],
            processing_records=[
                ExportedProcessingRecord(
                    id=r.id,
                    data_type=r.data_type,
                    purpose=r.purpose,
                    legal_basis=r.legal_basis,
                    collected_at=r.collected_at,
                    retention_expires_at=r.retention_expires_at,
                )
                for r in processing_records
            ],
        )
