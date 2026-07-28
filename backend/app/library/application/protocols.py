"""Repository interfaces for the Library bounded context.

These protocols define the contract between application and infrastructure layers.
Reference: ADR-0017 (cloud agnostic — all dependencies behind abstractions)
"""

from typing import Protocol
from uuid import UUID

from app.library.domain.entities import Book, Copy, ReadingStatus


class BookRepository(Protocol):
    """Persistence interface for Book."""

    def save(self, book: Book) -> Book: ...

    def find_by_id(self, book_id: UUID) -> Book | None: ...

    def find_by_user_copies(self, user_id: UUID) -> list[Book]: ...

    def find_by_group_members(self, member_ids: list[UUID]) -> list[Book]: ...

    def search(
        self, query: str, user_id: UUID, group_member_ids: list[UUID] | None = None
    ) -> list[Book]: ...

    def update(self, book: Book) -> Book: ...

    def delete(self, book_id: UUID) -> None: ...

    def has_copies(self, book_id: UUID) -> bool: ...


class CopyRepository(Protocol):
    """Persistence interface for Copy."""

    def save(self, copy: Copy) -> Copy: ...

    def find_by_id(self, copy_id: UUID) -> Copy | None: ...

    def find_by_user(self, user_id: UUID) -> list[Copy]: ...

    def find_by_book(self, book_id: UUID) -> list[Copy]: ...

    def update(self, copy: Copy) -> Copy: ...

    def delete(self, copy_id: UUID) -> None: ...


class FileStorage(Protocol):
    """Abstraction for file storage (MinIO, S3, local filesystem).

    Each user's files are isolated by prefix: users/{user_id}/
    Reference: ADR-0017, ADR-0009
    """

    def upload(self, user_id: UUID, filename: str, content: bytes) -> str:
        """Upload a file and return the storage reference (path/key)."""
        ...

    def download(self, file_ref: str) -> bytes:
        """Download file content by its reference."""
        ...

    def delete(self, file_ref: str) -> None:
        """Delete a file by its reference."""
        ...


class ReadingStatusRepository(Protocol):
    """Persistence interface for ReadingStatus.

    Reference: .kiro/specs/reading-status/design.md — Property 1, 2, 3
    """

    def upsert(self, reading_status: ReadingStatus) -> ReadingStatus: ...

    def find_by_user(self, user_id: UUID) -> list[ReadingStatus]: ...

    def find_by_user_and_book(
        self, user_id: UUID, book_id: UUID
    ) -> ReadingStatus | None: ...

    def delete(self, user_id: UUID, book_id: UUID) -> None: ...
