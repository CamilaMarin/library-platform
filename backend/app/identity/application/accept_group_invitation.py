"""AcceptGroupInvitation use case.

The ONLY path to MembershipStatus.ACCEPTED — enforces Property 2.
Reference: authentication/requirements.md Req 3.2, authentication/design.md Property 2
"""

from dataclasses import dataclass
from uuid import UUID

from app.identity.application.protocols import GroupMembershipRepository
from app.identity.domain.entities import GroupMembership, MembershipStatus


class InvitationNotFoundError(Exception):
    """Raised when the invitation/membership does not exist."""

    pass


class NotInviteeError(Exception):
    """Raised when the accepting user is not the invited user (403)."""

    pass


class AlreadyAcceptedError(Exception):
    """Raised when the membership is already in accepted status."""

    pass


@dataclass
class AcceptGroupInvitationInput:
    """Input DTO for AcceptGroupInvitation use case."""

    membership_id: UUID
    accepting_user_id: UUID


class AcceptGroupInvitation:
    """Accepts a group invitation — the ONLY path to accepted status.

    This enforces Property 2: a GroupMembership.status can only transition
    invited → accepted via an explicit action by the invited user_id.
    No other path exists.

    Reference: authentication/design.md Property 2
    """

    def __init__(self, group_membership_repository: GroupMembershipRepository):
        self._group_membership_repository = group_membership_repository

    def execute(self, input: AcceptGroupInvitationInput) -> GroupMembership:
        """Accept a group invitation.

        Raises:
            InvitationNotFoundError: if the membership does not exist.
            NotInviteeError: if accepting_user_id != membership.user_id (403).
            AlreadyAcceptedError: if the membership is already accepted.
        """
        # 1. Find membership by ID
        membership = self._group_membership_repository.find_by_id(input.membership_id)
        if membership is None:
            raise InvitationNotFoundError(f"Invitation {input.membership_id} not found")

        # 2. Verify accepting user is the invitee (Property 2)
        if input.accepting_user_id != membership.user_id:
            raise NotInviteeError("Only the invited user can accept this invitation")

        # 3. Verify status is INVITED (not already accepted)
        if membership.status == MembershipStatus.ACCEPTED:
            raise AlreadyAcceptedError("Invitation has already been accepted")

        # 4. Transition to ACCEPTED
        self._group_membership_repository.update_status(
            membership_id=membership.id,
            status=MembershipStatus.ACCEPTED,
        )

        # 5. Return updated membership
        membership.status = MembershipStatus.ACCEPTED
        return membership
