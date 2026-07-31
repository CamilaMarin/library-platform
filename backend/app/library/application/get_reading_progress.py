"""GetReadingProgress use case.

Retrieves the last saved reading position for a user's copy.
Reference: .kiro/specs/reader/requirements.md Req 2.2, design Property 2
"""

from uuid import UUID

from app.library.application.protocols import CopyRepository, ReadingProgressRepository
from app.library.domain.entities import ReadingProgress


class GetReadingProgress:
    """Retrieve reading progress for a specific copy owned by the user.

    Property 2: progress can only be read if user_id == copy.user_id.
    Returns None if no progress has been saved yet (user owns copy but hasn't started).
    Raises PermissionError if user doesn't own the copy.
    Raises ValueError if copy doesn't exist.
    """

    def __init__(
        self,
        copy_repository: CopyRepository,
        reading_progress_repository: ReadingProgressRepository,
    ):
        self._copies = copy_repository
        self._progress = reading_progress_repository

    def execute(self, copy_id: UUID, user_id: UUID) -> ReadingProgress | None:
        """Get reading progress for the given copy.

        Args:
            copy_id: The copy to retrieve progress for.
            user_id: The authenticated user making the request.

        Returns:
            ReadingProgress if exists, None if user owns copy but no progress saved.

        Raises:
            ValueError: If the copy does not exist.
            PermissionError: If user doesn't own the copy (403).
        """
        copy = self._copies.find_by_id(copy_id)
        if copy is None:
            raise ValueError(f"Copy {copy_id} not found")

        if copy.user_id != user_id:
            raise PermissionError("You do not have access to this copy")

        return self._progress.find_by_user_and_copy(user_id, copy_id)
