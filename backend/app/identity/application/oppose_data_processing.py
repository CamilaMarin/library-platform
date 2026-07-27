"""OpposeDataProcessing use case — allows a user to opt-out of non-essential data processing.

Implements the ARCO opposition right under Ley 21.719.
Users can object to specific purposes of data processing.

Reference: privacy/requirements.md Req 1.2
"""

from dataclasses import dataclass
from uuid import UUID

from app.identity.application.audit_service import AuditService
from app.identity.application.protocols import UserRepository
from app.identity.domain.entities import AuditAction


class UserNotFoundError(Exception):
    """Raised when the user does not exist."""

    pass


@dataclass
class OpposeResult:
    """Result of a successful opposition registration."""

    user_id: UUID
    processing_purpose: str
    opposed: bool


class OpposeDataProcessing:
    """Use case: register user's opposition to a specific data processing purpose.

    Updates the user's privacy_settings to record the opposition.
    The privacy_settings dict stores opposed purposes under an "opposed_purposes" key.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        audit_service: AuditService,
    ):
        self._user_repo = user_repository
        self._audit_service = audit_service

    def execute(self, user_id: UUID, processing_purpose: str) -> OpposeResult:
        """Register opposition to a specific processing purpose.

        Raises:
            UserNotFoundError: if user does not exist
        """
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")

        # Update privacy_settings to record the opposition
        privacy_settings = user.privacy_settings or {}
        opposed_purposes = privacy_settings.get("opposed_purposes", [])

        if processing_purpose not in opposed_purposes:
            opposed_purposes.append(processing_purpose)

        privacy_settings["opposed_purposes"] = opposed_purposes
        user.privacy_settings = privacy_settings

        self._user_repo.update(user)

        # Log ARCO opposition request
        self._audit_service.log(
            actor_user_id=user_id,
            action=AuditAction.ARCO_OPPOSE,
            affected_entity=f"user:{user_id}:oppose:{processing_purpose}",
        )

        return OpposeResult(
            user_id=user.id,
            processing_purpose=processing_purpose,
            opposed=True,
        )
