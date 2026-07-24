"""InviteGroupMember use case.

Invites a user to a family group. Only accepted members can invite.
Reference: authentication/requirements.md Req 3.1, 3.2
"""

from dataclasses import dataclass
from uuid import UUID

from app.identity.application.protocols import FamilyGroupRepository, GroupMembershipRepository
from app.identity.domain.entities import GroupMembership, MembershipStatus


class GroupNotFoundError(Exception):
    """Raised when the target group does not exist."""

    pass


class NotGroupMemberError(Exception):
    """Raised when the inviter is not an accepted member of the group."""

    pass


class AlreadyMemberError(Exception):
    """Raised when the invitee is already a member (invited or accepted)."""

    pass


@dataclass
class InviteGroupMemberInput:
    """Input DTO for InviteGroupMember use case."""

    group_id: UUID
    invitee_user_id: UUID
    inviter_user_id: UUID


class InviteGroupMember:
    """Invites a user to a family group.

    Only accepted members of the group can invite others.
    The invitee is added with status=INVITED (must accept explicitly).
    Reference: authentication/design.md Property 2
    """

    def __init__(
        self,
        family_group_repository: FamilyGroupRepository,
        group_membership_repository: GroupMembershipRepository,
    ):
        self._family_group_repository = family_group_repository
        self._group_membership_repository = group_membership_repository

    def execute(self, input: InviteGroupMemberInput) -> GroupMembership:
        """Invite a user to a family group.

        Raises:
            GroupNotFoundError: if the group does not exist.
            NotGroupMemberError: if the inviter is not an accepted member.
            AlreadyMemberError: if the invitee already has a membership record.
        """
        # 1. Verify group exists
        group = self._family_group_repository.find_by_id(input.group_id)
        if group is None:
            raise GroupNotFoundError(f"Group {input.group_id} not found")

        # 2. Verify inviter is an accepted member
        inviter_membership = self._group_membership_repository.find_by_user_and_group(
            user_id=input.inviter_user_id,
            group_id=input.group_id,
        )
        if inviter_membership is None or inviter_membership.status != MembershipStatus.ACCEPTED:
            raise NotGroupMemberError("Inviter is not an accepted member of this group")

        # 3. Verify invitee is not already a member
        existing = self._group_membership_repository.find_by_user_and_group(
            user_id=input.invitee_user_id,
            group_id=input.group_id,
        )
        if existing is not None:
            raise AlreadyMemberError("User is already a member or has a pending invitation")

        # 4. Create membership with INVITED status
        membership = GroupMembership(
            group_id=input.group_id,
            user_id=input.invitee_user_id,
            status=MembershipStatus.INVITED,
        )

        # 5. Save and return
        self._group_membership_repository.save(membership)
        return membership
