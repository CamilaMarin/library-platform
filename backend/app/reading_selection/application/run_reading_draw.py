"""RunReadingDraw use case.

Filters books by genre, max pages, unread (not previously drawn),
then validates availability for all participants. Selects random winner.

Reference: reading-selection/requirements.md Req 1, ADR-0008
"""

from dataclasses import dataclass
from uuid import UUID

from app.reading_selection.application.protocols import (
    BookQueryService,
    CopyQueryService,
    DrawRepository,
)
from app.reading_selection.domain.entities import Draw, check_availability, select_random_book


@dataclass
class RunDrawRequest:
    """Input for RunReadingDraw use case."""

    group_id: UUID
    participant_ids: list[UUID]
    genre: str | None = None
    max_pages: int | None = None
    unread_only: bool = False


class RunReadingDraw:
    """Use case: run a filtered random draw for a family group.

    1. Find books accessible to group members (filtered by genre/pages)
    2. Exclude previously drawn books if unread_only
    3. Validate availability for ALL participants (ADR-0008)
    4. Randomly select from candidates
    5. Record the draw result
    """

    def __init__(
        self,
        draw_repository: DrawRepository,
        book_query: BookQueryService,
        copy_query: CopyQueryService,
    ):
        self._draw_repo = draw_repository
        self._book_query = book_query
        self._copy_query = copy_query

    def execute(self, request: RunDrawRequest) -> Draw:
        """Execute the draw. Returns Draw with result (or None if no candidates)."""
        # 1. Find candidate books (filtered)
        books = self._book_query.find_books_by_group_members(
            member_ids=request.participant_ids,
            genre=request.genre,
            max_pages=request.max_pages,
        )

        if not books:
            return self._save_empty_draw(request)

        # 2. Exclude previously drawn if unread_only
        candidate_book_ids = [b.id for b in books]
        if request.unread_only:
            previously_drawn = self._draw_repo.find_result_book_ids_by_group(
                request.group_id
            )
            candidate_book_ids = [
                bid for bid in candidate_book_ids if bid not in previously_drawn
            ]

        if not candidate_book_ids:
            return self._save_empty_draw(request)

        # 3. Validate availability for all participants
        copies_by_book = self._copy_query.find_copies_for_books(
            book_ids=candidate_book_ids,
            participant_ids=request.participant_ids,
        )

        available_book_ids = []
        for book_id in candidate_book_ids:
            copies = copies_by_book.get(book_id, [])
            if check_availability(copies, request.participant_ids):
                available_book_ids.append(book_id)

        if not available_book_ids:
            return self._save_empty_draw(request)

        # 4. Random selection
        selected_book_id = select_random_book(available_book_ids)

        # Find source user (who owns a copy of this book)
        source_user_id = None
        if selected_book_id:
            copies = copies_by_book.get(selected_book_id, [])
            if copies:
                source_user_id = copies[0].user_id

        # 5. Save draw result
        draw = Draw(
            group_id=request.group_id,
            filters={
                "genre": request.genre,
                "max_pages": request.max_pages,
                "unread_only": request.unread_only,
            },
            participants=request.participant_ids,
            result_book_id=selected_book_id,
            result_source_user_id=source_user_id,
        )
        return self._draw_repo.save(draw)

    def _save_empty_draw(self, request: RunDrawRequest) -> Draw:
        """Save a draw with no result (no candidates matched)."""
        draw = Draw(
            group_id=request.group_id,
            filters={
                "genre": request.genre,
                "max_pages": request.max_pages,
                "unread_only": request.unread_only,
            },
            participants=request.participant_ids,
            result_book_id=None,
            result_source_user_id=None,
        )
        return self._draw_repo.save(draw)
