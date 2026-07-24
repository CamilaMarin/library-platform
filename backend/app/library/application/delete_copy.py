"""DeleteCopy use case.

Deletes a copy. If digital, also deletes the file from storage.
Only the owner can delete their copy.

Reference: library/requirements.md Req 1.5, ADR-0009
"""

from uuid import UUID

from app.library.application.protocols import CopyRepository, FileStorage
from app.library.domain.entities import CopyType


class DeleteCopy:
    """Use case: delete a copy.

    Owner-only. Digital copies also have their file removed from storage.
    """

    def __init__(
        self,
        copy_repository: CopyRepository,
        file_storage: FileStorage | None = None,
    ):
        self._copy_repo = copy_repository
        self._file_storage = file_storage

    def execute(self, copy_id: UUID, user_id: UUID) -> None:
        """Delete a copy. Validates ownership. Removes file if digital."""
        copy = self._copy_repo.find_by_id(copy_id)
        if not copy:
            raise ValueError(f"Copy {copy_id} not found")

        if copy.user_id != user_id:
            raise PermissionError("Cannot delete a copy you don't own")

        # If digital, delete the file from storage
        if copy.type == CopyType.DIGITAL and copy.file_ref and self._file_storage:
            self._file_storage.delete(copy.file_ref)

        self._copy_repo.delete(copy_id)
