"""SetReadingStatus use case.

Upserts the personal reading status for a (user_id, book_id) pair.
Reference: .kiro/specs/reading-status/requirements.md Req 1, design Property 1 & 2
"""

from dataclasses import dataclass
from uuid import UUID

from app.library.application.protocols import BookRepository, ReadingStatusRepository
from app.library.domain.entities import ReadingStatus, ReadingStatusValue


@dataclass
class SetReadingStatusRequest:
    user_id: UUID
    book_id: UUID
    status: ReadingStatusValue


class SetReadingStatus:
    """Upsert a reading status for a (user, book) pair.

    Validates the book exists before writing (Req 1 — 404 book_not_found).
    Property 2: only affects the record whose user_id matches the caller.
    """

    def __init__(
        self,
        reading_status_repository: ReadingStatusRepository,
        book_repository: BookRepository,
    ):
        self._statuses = reading_status_repository
        self._books = book_repository

    def execute(self, request: SetReadingStatusRequest) -> ReadingStatus:
        book = self._books.find_by_id(request.book_id)
        if book is None:
            raise ValueError("book_not_found")

        record = ReadingStatus(
            user_id=request.user_id,
            book_id=request.book_id,
            status=request.status,
        )
        return self._statuses.upsert(record)
