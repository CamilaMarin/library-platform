"""RectifyUserData use case — allows a user to update their name and/or email.

Implements the ARCO rectification right under Ley 21.719.
Users can correct inaccurate personal data held by the system.

Reference: privacy/requirements.md Req 1.2
"""

import re
from dataclasses import dataclass
from uuid import UUID

from app.identity.application.audit_service import AuditService
from app.identity.application.protocols import UserRepository
from app.identity.domain.entities import AuditAction


class UserNotFoundError(Exception):
    """Raised when the user does not exist."""

    pass


class NoFieldsProvidedError(Exception):
    """Raised when neither name nor email is provided for rectification."""

    pass


class EmailAlreadyTakenError(Exception):
    """Raised when the requested email is already in use by another user."""

    pass


class InvalidEmailError(Exception):
    """Raised when the provided email format is invalid."""

    pass


@dataclass
class RectifyResult:
    """Result of a successful rectification."""

    user_id: UUID
    name: str
    email: str


# Simple email regex — same level of validation as registration
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RectifyUserData:
    """Use case: update user's name and/or email (ARCO rectification right).

    Validates:
    - At least one field (name or email) must be provided
    - Email format must be valid if provided
    - Email must not already be taken by another user
    """

    def __init__(
        self,
        user_repository: UserRepository,
        audit_service: AuditService,
    ):
        self._user_repo = user_repository
        self._audit_service = audit_service

    def execute(
        self,
        user_id: UUID,
        new_name: str | None = None,
        new_email: str | None = None,
    ) -> RectifyResult:
        """Rectify user data by updating name and/or email.

        Raises:
            UserNotFoundError: if user does not exist
            NoFieldsProvidedError: if neither name nor email is provided
            InvalidEmailError: if email format is invalid
            EmailAlreadyTakenError: if email is already used by another user
        """
        if not new_name and not new_email:
            raise NoFieldsProvidedError("At least one field (name or email) must be provided")

        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")

        # Validate email format if provided
        if new_email:
            if not _EMAIL_PATTERN.match(new_email):
                raise InvalidEmailError(f"Invalid email format: {new_email}")

            # Check email uniqueness (only if different from current)
            if new_email != user.email:
                existing = self._user_repo.find_by_email(new_email)
                if existing is not None:
                    raise EmailAlreadyTakenError(f"Email {new_email} is already in use")

        # Apply updates
        if new_name:
            user.name = new_name
        if new_email:
            user.email = new_email

        self._user_repo.update(user)

        # Log ARCO rectification request
        self._audit_service.log(
            actor_user_id=user_id,
            action=AuditAction.ARCO_RECTIFY,
            affected_entity=f"user:{user_id}:rectify",
        )

        return RectifyResult(
            user_id=user.id,
            name=user.name,
            email=user.email,
        )
