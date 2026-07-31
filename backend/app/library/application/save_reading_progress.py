"""SaveReadingProgress use case.

Upserts reading progress for a user's digital copy.
Reference: .kiro/specs/reader/design.md — Property 2 (isolation), Property 3 (idempotent)
"""

from dataclasses import dataclass
from uuid import UUID

from app.library.application.protocols import (
    BookRepository,
    CopyRepository,
    ReadingProgressRepository,
    ReadingStatusRepository,
)
from app.library.domain.entities import (
    CopyType,
    FileFormat,
    ReadingProgress,
    ReadingStatus,
    ReadingStatusValue,
)


@dataclass
class SaveReadingProgressRequest:
    """Input for SaveReadingProgress use case."""

    copy_id: UUID
    user_id: UUID
    position: str
    percentage: float
    file_format: FileFormat


class SaveReadingProgress:
    """Upserts reading progress for a user+copy pair.

    Validates:
    - Copy exists
    - User owns the copy (Property 2: progress isolation)
    - Copy is digital (progress only applies to digital copies)
    - Position format is valid for the file format (delegated to entity)

    Idempotent: same position just updates last_read_at (Property 3).
    """

    def __init__(
        self,
        copy_repository: CopyRepository,
        reading_progress_repository: ReadingProgressRepository,
        reading_status_repository: ReadingStatusRepository | None = None,
        book_repository: BookRepository | None = None,
    ) -> None:
        self._copy_repo = copy_repository
        self._progress_repo = reading_progress_repository
        self._status_repo = reading_status_repository
        self._book_repo = book_repository

    def execute(self, request: SaveReadingProgressRequest) -> ReadingProgress:
        # 1. Validate copy exists
        copy = self._copy_repo.find_by_id(request.copy_id)
        if copy is None:
            raise ValueError(f"Copy {request.copy_id} not found")

        # 2. Validate ownership (Property 2: progress isolation)
        ReadingProgress.validate_ownership(request.user_id, copy.user_id)

        # 3. Validate copy is digital
        if copy.type != CopyType.DIGITAL:
            raise ValueError("Reading progress is only available for digital copies")

        # 4. Create/update ReadingProgress entity
        #    Entity __post_init__ validates position format (Property 4)
        progress = ReadingProgress(
            user_id=request.user_id,
            copy_id=request.copy_id,
            position=request.position,
            file_format=request.file_format,
            percentage=request.percentage,
        )

        # 5. Persist via upsert (Property 3: idempotent)
        result = self._progress_repo.upsert(progress)

        # 6. Sync with ReadingStatus.current_page for library preview bar.
        if self._status_repo:
            self._sync_reading_status(request, copy)

        return result

    def _sync_reading_status(self, request: SaveReadingProgressRequest, copy) -> None:
        """Sync ReadingStatus.current_page from reader progress.

        PDF: position is the page number directly.
        EPUB: calculate page from percentage × book.pages (if book has pages set).
        Only updates if status is "reading" or no status exists.
        """
        try:
            page_number: int | None = None

            if request.file_format == FileFormat.PDF:
                page_number = int(request.position)
            elif request.file_format == FileFormat.EPUB and self._book_repo:
                book = self._book_repo.find_by_id(copy.book_id)
                if book and book.pages and request.percentage > 0:
                    page_number = max(1, round(request.percentage * book.pages))

            if page_number is None:
                return

            existing = self._status_repo.find_by_user_and_book(
                request.user_id, copy.book_id
            )
            # Only update if currently reading or no status set yet.
            if existing is None or existing.status == ReadingStatusValue.READING:
                record = ReadingStatus(
                    user_id=request.user_id,
                    book_id=copy.book_id,
                    status=ReadingStatusValue.READING,
                    current_page=page_number,
                )
                self._status_repo.upsert(record)
        except (ValueError, TypeError):
            pass  # Skip sync on any conversion error
