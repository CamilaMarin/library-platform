"""DeleteUserAccount use case — permanently deletes all identity-owned data for a user.

Integrates with the Privacy module's ARCO (cancellation) right.
MVP: hard-delete, no recovery period.

Reference: authentication/requirements.md Req 4.1, 4.2
"""

from uuid import UUID

from app.identity.application.audit_service import AuditService
from app.identity.application.protocols import (
    DataConsentRepository,
    DataProcessingRecordRepository,
    GroupMembershipRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.identity.domain.entities import AuditAction


class UserNotFoundError(Exception):
    """Raised when the user does not exist."""

    pass


class DeleteUserAccount:
    """Use case: permanently delete a user account and all associated identity data.

    Order of operations:
    1. Verify user exists
    2. Revoke all active refresh tokens
    3. Delete group memberships
    4. Delete data consents
    5. Delete data processing records
    6. Delete the user record
    7. Log ACCOUNT_DELETED audit entry (anonymized actor)
    """

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        membership_repository: GroupMembershipRepository,
        consent_repository: DataConsentRepository,
        processing_record_repository: DataProcessingRecordRepository,
        audit_service: AuditService,
    ):
        self._user_repo = user_repository
        self._refresh_token_repo = refresh_token_repository
        self._membership_repo = membership_repository
        self._consent_repo = consent_repository
        self._processing_record_repo = processing_record_repository
        self._audit_service = audit_service

    def execute(self, user_id: UUID) -> None:
        """Delete user account and all associated identity-owned data.

        Raises UserNotFoundError if user does not exist.
        """
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")

        # Revoke all active refresh tokens
        self._refresh_token_repo.revoke_all_by_user_id(user_id)

        # Delete group memberships
        self._membership_repo.delete_by_user_id(user_id)

        # Delete data consents
        self._consent_repo.delete_by_user_id(user_id)

        # Delete data processing records
        self._processing_record_repo.delete_by_user_id(user_id)

        # Delete the user record
        self._user_repo.delete(user_id)

        # Log ACCOUNT_DELETED audit entry
        # The user_id is kept in the audit log as legal record of deletion,
        # but the User record itself is gone.
        self._audit_service.log(
            actor_user_id=user_id,
            action=AuditAction.ACCOUNT_DELETED,
            affected_entity=f"user:{user_id}:deleted",
        )
