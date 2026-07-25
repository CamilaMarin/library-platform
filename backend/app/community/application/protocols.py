"""Repository interfaces for the Community bounded context.

Reference: ADR-0017 (all dependencies behind abstractions)
"""

from typing import Protocol
from uuid import UUID

from app.community.domain.entities import Club, Comment, ReadingTurn


class ClubRepository(Protocol):
    """Persistence interface for Club."""

    def save(self, club: Club) -> Club: ...

    def find_by_id(self, club_id: UUID) -> Club | None: ...

    def update(self, club: Club) -> Club: ...


class ReadingTurnRepository(Protocol):
    """Persistence interface for ReadingTurn."""

    def save(self, turn: ReadingTurn) -> ReadingTurn: ...

    def find_by_club(self, club_id: UUID) -> list[ReadingTurn]: ...


class CommentRepository(Protocol):
    """Persistence interface for Comment."""

    def save(self, comment: Comment) -> Comment: ...

    def find_by_turn(self, turn_id: UUID) -> list[Comment]: ...


class CopyOwnershipQuery(Protocol):
    """Read-only query into Library context for copy ownership.

    Never returns file_ref — only checks ownership exists.
    Reference: ADR-0009 (cross-context: never returns file_ref)
    """

    def user_owns_copy_of_book(self, user_id: UUID, book_id: UUID) -> bool:
        """Check if user owns any copy (physical or digital) of the book."""
        ...
