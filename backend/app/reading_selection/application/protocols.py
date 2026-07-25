"""Repository interfaces for Reading Selection.

Reference: ADR-0017 (all dependencies behind abstractions)
"""

from typing import Protocol
from uuid import UUID

from app.library.domain.entities import Book, Copy
from app.reading_selection.domain.entities import Draw, TurnHistory


class DrawRepository(Protocol):
    """Persistence interface for Draw."""

    def save(self, draw: Draw) -> Draw: ...

    def find_by_group(self, group_id: UUID) -> list[Draw]: ...

    def find_result_book_ids_by_group(self, group_id: UUID) -> list[UUID]: ...


class TurnHistoryRepository(Protocol):
    """Persistence interface for TurnHistory."""

    def find_by_group(self, group_id: UUID) -> list[TurnHistory]: ...

    def save_or_update(self, turn: TurnHistory) -> TurnHistory: ...


class CopyQueryService(Protocol):
    """Read-only query into Library context for copy availability.

    Never returns file_ref — only id, user_id, book_id, type, status.
    """

    def find_copies_for_books(
        self, book_ids: list[UUID], participant_ids: list[UUID]
    ) -> dict[UUID, list[Copy]]:
        """Returns copies grouped by book_id for the given participants."""
        ...


class BookQueryService(Protocol):
    """Read-only query for books accessible to a group."""

    def find_books_by_group_members(
        self,
        member_ids: list[UUID],
        genre: str | None = None,
        max_pages: int | None = None,
    ) -> list[Book]:
        """Find books with copies owned by group members, optionally filtered."""
        ...
