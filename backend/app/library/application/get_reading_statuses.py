"""GetReadingStatuses use case.

Returns all reading statuses for a given user.
Reference: .kiro/specs/reading-status/requirements.md Req 2, design Property 3
"""

from uuid import UUID

from app.library.application.protocols import ReadingStatusRepository
from app.library.domain.entities import ReadingStatus


class GetReadingStatuses:
    """Retrieve all (book_id, status) pairs for the authenticated user.

    Property 3: only returns records where user_id == caller's user_id.
    """

    def __init__(self, reading_status_repository: ReadingStatusRepository):
        self._statuses = reading_status_repository

    def execute(self, user_id: UUID) -> list[ReadingStatus]:
        return self._statuses.find_by_user(user_id)
