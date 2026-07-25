"""Infrastructure implementation of MembershipChecker.

Queries identity (family_groups, group_memberships) and community (clubs) tables
to verify user membership for review access control.

Reference: reviews/design.md Properties 3, 5; ADR-0007
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.community.infrastructure.models import ClubModel
from app.identity.infrastructure.models import GroupMembershipModel


class SqlMembershipChecker:
    """SQL-based membership verification for review access control.

    - Group membership: checks group_memberships table for active membership.
    - Club membership: a club belongs to a family group; club members are
      the members of that group (clubs table has group_id FK).
    """

    def __init__(self, session: Session):
        self._session = session

    def is_member_of_group(self, user_id: UUID, group_id: UUID) -> bool:
        """Check if user is an active member of the family group."""
        exists = (
            self._session.query(GroupMembershipModel)
            .filter(
                GroupMembershipModel.user_id == user_id,
                GroupMembershipModel.group_id == group_id,
                GroupMembershipModel.status == "accepted",
            )
            .first()
        )
        return exists is not None

    def is_member_of_club(self, user_id: UUID, club_id: UUID) -> bool:
        """Check if user is a member of the club via its parent group.

        A club belongs to a single family group (ADR-0006). Club members
        are all accepted members of that group.
        """
        club = self._session.get(ClubModel, club_id)
        if club is None:
            return False

        return self.is_member_of_group(user_id, club.group_id)
