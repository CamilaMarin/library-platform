"""CreateClub use case.

Creates a book club within a single family group.
Reference: clubs/requirements.md Req 1.1, ADR-0006
"""

from uuid import UUID

from app.community.application.protocols import ClubRepository
from app.community.domain.entities import Club


class CreateClub:
    """Use case: create a club (single group only, ADR-0006)."""

    def __init__(self, club_repository: ClubRepository):
        self._club_repo = club_repository

    def execute(self, group_id: UUID, name: str) -> Club:
        """Create a new club associated with a family group."""
        club = Club(group_id=group_id, name=name)
        return self._club_repo.save(club)
