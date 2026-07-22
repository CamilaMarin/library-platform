"""Identity & Privacy domain entities.

These are pure domain objects — no framework or infrastructure imports.
Reference: ADR-0003 (Ley 21.719 compliance), ADR-0016 (configurable retention)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditAction(str, Enum):
    """Actions tracked by the audit log (MVP: high-value operations only)."""

    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"
    ACCOUNT_DELETED = "account_deleted"
    FILE_UPLOADED = "file_uploaded"
    ARCO_REQUEST = "arco_request"


@dataclass
class DataConsent:
    """Record of a user's explicit consent to data processing.

    A User cannot be created without a corresponding DataConsent.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    timestamp: datetime = field(default_factory=_utcnow)
    policy_version: str = ""
    purpose: str = ""

    def __post_init__(self):
        if not self.policy_version:
            raise ValueError("DataConsent requires a policy_version")
        if not self.purpose:
            raise ValueError("DataConsent requires a purpose")


@dataclass
class DataProcessingRecord:
    """Log of what personal data is processed, why, and for how long.

    Required by Ley 21.719 for auditability.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    data_type: str = ""
    purpose: str = ""
    legal_basis: str = ""
    collected_at: datetime = field(default_factory=_utcnow)
    retention_expires_at: datetime | None = None


@dataclass
class AuditLog:
    """Record of a high-value operation on personal data.

    MVP scope: registration, login, account deletion, file upload, ARCO requests.
    Design is extensible — adding operations means adding enum values.
    """

    id: UUID = field(default_factory=uuid4)
    actor_user_id: UUID | None = None
    action: AuditAction = AuditAction.USER_REGISTERED
    affected_entity: str = ""
    timestamp: datetime = field(default_factory=_utcnow)


@dataclass
class RetentionPolicy:
    """Configurable data retention policy.

    Duration is read from database at runtime — never hardcoded.
    No automated job in MVP — entity and config table only.
    Reference: ADR-0016
    """

    id: UUID = field(default_factory=uuid4)
    data_type: str = ""
    duration_days: int = 365
    description: str = ""
    active: bool = True
