"""CreateCopy use case.

Creates a Copy (physical or digital) associated with an existing Book.
Digital copies require file upload via FileStorage interface.

Reference: library/requirements.md Req 1.2, 1.3, 1.4
           ADR-0001 (no file sharing), ADR-0009 (digital isolation)
"""

from dataclasses import dataclass
from uuid import UUID

from app.library.application.protocols import BookRepository, CopyRepository, FileStorage
from app.library.domain.entities import Copy, CopyType


@dataclass
class CreatePhysicalCopyRequest:
    """Input for creating a physical copy."""

    book_id: UUID
    user_id: UUID


@dataclass
class CreateDigitalCopyRequest:
    """Input for creating a digital copy with file upload."""

    book_id: UUID
    user_id: UUID
    filename: str
    content: bytes


ALLOWED_EXTENSIONS = {".epub", ".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class CreateCopy:
    """Use case: create a copy (physical or digital).

    Physical: metadata + status only, no file.
    Digital: uploads file to isolated per-user storage (ADR-0009).
    """

    def __init__(
        self,
        copy_repository: CopyRepository,
        book_repository: BookRepository,
        file_storage: FileStorage | None = None,
    ):
        self._copy_repo = copy_repository
        self._book_repo = book_repository
        self._file_storage = file_storage

    def create_physical(self, request: CreatePhysicalCopyRequest) -> Copy:
        """Create a physical copy (no file)."""
        self._validate_book_exists(request.book_id)

        copy = Copy(
            user_id=request.user_id,
            book_id=request.book_id,
            type=CopyType.PHYSICAL,
            file_ref=None,
        )
        return self._copy_repo.save(copy)

    def create_digital(self, request: CreateDigitalCopyRequest) -> Copy:
        """Create a digital copy with file upload.

        Validates: file extension (EPUB/PDF only), file size, book exists.
        Stores file in per-user isolated storage (ADR-0009).
        """
        if not self._file_storage:
            raise RuntimeError("FileStorage not configured for digital copies")

        self._validate_book_exists(request.book_id)
        self._validate_file(request.filename, request.content)

        # Upload to isolated per-user storage
        file_ref = self._file_storage.upload(
            user_id=request.user_id,
            filename=request.filename,
            content=request.content,
        )

        copy = Copy(
            user_id=request.user_id,
            book_id=request.book_id,
            type=CopyType.DIGITAL,
            file_ref=file_ref,
        )
        return self._copy_repo.save(copy)

    def _validate_book_exists(self, book_id: UUID) -> None:
        book = self._book_repo.find_by_id(book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")

    def _validate_file(self, filename: str, content: bytes) -> None:
        # Check extension
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Check size
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {len(content)} bytes. Maximum: {MAX_FILE_SIZE} bytes"
            )
