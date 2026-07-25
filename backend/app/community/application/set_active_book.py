"""SetActiveBook use case.

Assigns an active book and optional discussion date to a club.
Reference: clubs/requirements.md Req 1.2
"""

from datetime import datetime
from uuid import UUID

from app.community.application.protocols import ClubRepository


class SetActiveBook:
    """Use case: set the club's active book and discussion date."""

    def __init__(self, club_repository: ClubRepository):
        self._club_repo = club_repository

    def execute(
        self, club_id: UUID, book_id: UUID, discussion_date: datetime | None = None
    ) -> None:
        """Set active book for the club."""
        club = self._club_repo.find_by_id(club_id)
        if not club:
            raise ValueError(f"Club {club_id} not found")

        club.active_book_id = book_id
        club.discussion_date = discussion_date
        self._club_repo.update(club)
