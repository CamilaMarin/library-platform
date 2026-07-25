"""ActivateReadingTurn use case.

Validates that the user owns their own copy of the book before activating.
Never transfers the file — only coordinates who reads/comments.

Reference: clubs/requirements.md Req 1.4, 2.1, 2.2
           clubs/design.md Property 1
           ADR-0001, ADR-0009
"""

from uuid import UUID

from app.community.application.protocols import (
    ClubRepository,
    CopyOwnershipQuery,
    ReadingTurnRepository,
)
from app.community.domain.entities import ReadingTurn


class CopyOwnershipError(Exception):
    """Raised when user doesn't own a copy of the book."""

    pass


class ActivateReadingTurn:
    """Use case: activate a reading turn for a user.

    Property 1: succeeds ONLY if user owns a Copy of the book.
    Never provides file access — only coordinates order/comments.
    """

    def __init__(
        self,
        club_repository: ClubRepository,
        turn_repository: ReadingTurnRepository,
        copy_ownership: CopyOwnershipQuery,
    ):
        self._club_repo = club_repository
        self._turn_repo = turn_repository
        self._copy_ownership = copy_ownership

    def execute(self, club_id: UUID, user_id: UUID) -> ReadingTurn:
        """Activate a reading turn. Validates copy ownership first."""
        club = self._club_repo.find_by_id(club_id)
        if not club:
            raise ValueError(f"Club {club_id} not found")

        if not club.active_book_id:
            raise ValueError("Club has no active book set")

        # Property 1: validate user owns a copy
        if not self._copy_ownership.user_owns_copy_of_book(user_id, club.active_book_id):
            raise CopyOwnershipError(
                f"User {user_id} does not own a copy of book {club.active_book_id}. "
                "Add the book to your library first."
            )

        turn = ReadingTurn(
            club_id=club_id,
            book_id=club.active_book_id,
            current_user_id=user_id,
        )
        return self._turn_repo.save(turn)
