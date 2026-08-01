"""GetUserOppositions use case — returns the list of active ARCO oppositions for a user.

Implements the ARCO opposition right (read) under Ley 21.719.
Reads `privacy_settings["opposed_purposes"]` without modifying any data.

Reference: view-registered-oppositions/requirements.md Req 2.3
"""

from uuid import UUID

from app.identity.application.audit_service import AuditService
from app.identity.application.protocols import UserRepository
from app.identity.domain.entities import AuditAction


class UserNotFoundError(Exception):
    """Raised when the user does not exist."""

    pass


class GetUserOppositions:
    """Use case: retrieve the list of data processing purposes the user has opposed.

    Reads `privacy_settings["opposed_purposes"]` from the User entity.
    Logs an ARCO_REQUEST audit entry (read operation — consistent with ExportUserData).
    Does not modify any data.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        audit_service: AuditService,
    ):
        self._user_repo = user_repository
        self._audit_service = audit_service

    def execute(self, user_id: UUID) -> list[str]:
        """Return the list of opposed processing purposes for the given user.

        Raises:
            UserNotFoundError: if user does not exist
        """
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")

        # Log ARCO read access (reuses ARCO_REQUEST, consistent with ExportUserData)
        self._audit_service.log(
            actor_user_id=user_id,
            action=AuditAction.ARCO_REQUEST,
            affected_entity=f"user:{user_id}:oppositions",
        )

        return (user.privacy_settings or {}).get("opposed_purposes", [])
