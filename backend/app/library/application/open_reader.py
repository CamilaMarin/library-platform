"""OpenReader use case.

Validates ownership and serves the digital file content to the authenticated owner.
NEVER returns 404 for non-owned copies — always 403 to prevent information leakage.

Reference: reader/requirements.md Req 1.1, 1.2, 1.3, 1.5
Reference: ADR-0001, ADR-0009, ADR-0014
"""

from uuid import UUID

from app.library.application.protocols import CopyRepository, FileStorage
from app.library.domain.entities import CopyType


class OpenReader:
    """Use case: open a digital copy for reading.

    Validates:
    - The copy exists and belongs to the requesting user (ownership gate).
    - The copy is digital (physical copies have no file).

    Returns the file content bytes from FileStorage.
    Security: always returns 403 (never 404) for non-owned copies
    to avoid leaking existence information.
    """

    def __init__(
        self,
        copy_repository: CopyRepository,
        file_storage: FileStorage,
    ):
        self._copy_repo = copy_repository
        self._file_storage = file_storage

    def execute(self, copy_id: UUID, request_user_id: UUID) -> bytes:
        """Open a digital copy for reading.

        Args:
            copy_id: The ID of the copy to open.
            request_user_id: The authenticated user making the request.

        Returns:
            The file content as bytes.

        Raises:
            PermissionError: If the copy doesn't exist or doesn't belong to the user.
                Always 403, never 404 — prevents information leakage (ADR-0009).
            ValueError: If the copy is physical (no file to serve).
        """
        copy = self._copy_repo.find_by_id(copy_id)

        # Ownership gate: NEVER expose whether a copy exists to non-owners.
        # Both "not found" and "not owned" return the same error (403).
        if copy is None or copy.user_id != request_user_id:
            raise PermissionError("Access denied")

        # Physical copies have no file to serve
        if copy.type != CopyType.DIGITAL:
            raise ValueError("Cannot open reader for a physical copy")

        # TODO: Add a stream() method to FileStorage protocol for large files
        # to avoid loading the entire file into memory. For MVP, download() is acceptable.
        return self._file_storage.download(copy.file_ref)
