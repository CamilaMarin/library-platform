"""CreateFamilyGroup use case.

Creates a family group and automatically adds the creator as an accepted member.
Reference: authentication/requirements.md Req 3.1
"""

from dataclasses import dataclass
from uuid import UUID

from app.identity.application.protocols import FamilyGroupRepository, GroupMembershipRepository
from app.identity.domain.entities import FamilyGroup, GroupMembership, MembershipStatus


@dataclass
class CreateFamilyGroupInput:
    """Input DTO for CreateFamilyGroup use case."""

    name: str
    creator_user_id: UUID


class CreateFamilyGroup:
    """Creates a family group and adds the creator as an accepted member."""

    def __init__(
        self,
        family_group_repository: FamilyGroupRepository,
        group_membership_repository: GroupMembershipRepository,
    ):
        self._family_group_repository = family_group_repository
        self._group_membership_repository = group_membership_repository

    def execute(self, input: CreateFamilyGroupInput) -> FamilyGroup:
        """Create a new family group.

        The creator is automatically added as a member with status=accepted.
        Raises ValueError if name is empty (domain validation).
        """
        group = FamilyGroup(name=input.name)

        self._family_group_repository.save(group)

        membership = GroupMembership(
            group_id=group.id,
            user_id=input.creator_user_id,
            status=MembershipStatus.ACCEPTED,
        )
        self._group_membership_repository.save(membership)

        return group
