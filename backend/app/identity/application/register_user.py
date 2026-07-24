"""RegisterUser use case — creates a User + DataConsent in the same transaction.

Consent-gating invariant: a User row is NEVER created without a DataConsent row.
If consent data is missing, registration is rejected with no partial records.

Reference: authentication/requirements.md Req 1, design.md Property 1
"""

from dataclasses import dataclass

import bcrypt

from app.identity.application.audit_service import AuditService
from app.identity.application.protocols import DataConsentRepository, UserRepository
from app.identity.domain.entities import AuditAction, DataConsent, User


class EmailAlreadyExistsError(Exception):
    """Raised when attempting to register with an email that is already in use."""

    pass


class ConsentRequiredError(Exception):
    """Raised when registration is attempted without consent data."""

    pass


@dataclass
class RegisterUserInput:
    """Input DTO for the RegisterUser use case."""

    name: str
    email: str
    password: str
    consent_policy_version: str
    consent_purpose: str


class RegisterUser:
    """Use case: register a new user with explicit consent.

    Enforces the consent-gating invariant — User and DataConsent
    are created in the same transaction or not at all.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        consent_repository: DataConsentRepository,
        audit_service: AuditService,
    ):
        self._user_repo = user_repository
        self._consent_repo = consent_repository
        self._audit_service = audit_service

    def execute(self, input: RegisterUserInput) -> User:
        """Register a user with consent. Returns the created User (no password_hash exposed)."""
        # Validate consent data is present
        if not input.consent_policy_version or not input.consent_purpose:
            raise ConsentRequiredError(
                "Explicit consent (policy_version and purpose) is required for registration"
            )

        # Check for duplicate email
        existing = self._user_repo.find_by_email(input.email)
        if existing is not None:
            raise EmailAlreadyExistsError(
                f"A user with email '{input.email}' already exists"
            )

        # Hash password with bcrypt — never store plain text
        password_hash = bcrypt.hashpw(
            input.password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        # Create User entity
        user = User(
            name=input.name,
            email=input.email,
            password_hash=password_hash,
        )

        # Create DataConsent entity (consent-gating: same transaction)
        consent = DataConsent(
            user_id=user.id,
            policy_version=input.consent_policy_version,
            purpose=input.consent_purpose,
        )

        # Persist both in the same transaction (flush, no commit — caller manages tx)
        self._consent_repo.save(consent)
        self._user_repo.save(user)

        # Audit the registration
        self._audit_service.log(
            actor_user_id=user.id,
            action=AuditAction.USER_REGISTERED,
            affected_entity=f"user:{user.id}",
        )

        # Return user without exposing password_hash
        return User(
            id=user.id,
            name=user.name,
            email=user.email,
            password_hash="",  # Never expose hash to caller
            privacy_settings=user.privacy_settings,
            created_at=user.created_at,
        )
