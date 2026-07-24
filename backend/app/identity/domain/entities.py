"""Identity & Privacy domain entities.

These are pure domain objects — no framework or infrastructure imports.
Reference: ADR-0003 (Ley 21.719 compliance), ADR-0004 (JWT), ADR-0016 (configurable retention)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Privacy entities (M0) ---


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


# --- Authentication entities (M1) ---


@dataclass
class User:
    """Aggregate root for the Identity bounded context.

    Password is stored as a bcrypt hash — never plain text.
    Reference: ADR-0004, authentication/requirements.md Req 1.3
    """

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    email: str = ""
    password_hash: str = ""
    privacy_settings: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        if not self.email:
            raise ValueError("User requires an email")
        if not self.name:
            raise ValueError("User requires a name")


@dataclass
class RefreshToken:
    """Long-lived token for obtaining new Access Tokens without re-login.

    Rotation: issuing a new token always invalidates the previous one (atomic).
    Reference: ADR-0004, authentication/design.md Property 4
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    token_hash: str = ""
    expires_at: datetime = field(default_factory=_utcnow)
    revoked: bool = False
    created_at: datetime = field(default_factory=_utcnow)

    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        # Handle timezone-naive datetimes (e.g. from SQLite) by assuming UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now >= expires_at

    @property
    def is_usable(self) -> bool:
        return not self.revoked and not self.is_expired
