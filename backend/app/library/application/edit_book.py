"""EditBook use case.

Updates book metadata. Any authenticated user can edit books they created.
Reference: library/requirements.md Req 1.5
"""

from dataclasses import dataclass
from uuid import UUID

from app.library.application.protocols import BookRepository
from app.library.domain.entities import Book


@dataclass
class EditBookRequest:
    """Input for EditBook use case."""

    book_id: UUID
    title: str | None = None
    author: str | None = None
    genres: list[str] | None = None
    description: str | None = None
    pages: int | None = None
    isbn: str | None = None


class EditBook:
    """Use case: edit a book's metadata."""

    def __init__(self, book_repository: BookRepository):
        self._book_repo = book_repository

    def execute(self, request: EditBookRequest) -> Book:
        """Update book metadata. Only provided fields are changed."""
        book = self._book_repo.find_by_id(request.book_id)
        if not book:
            raise ValueError(f"Book {request.book_id} not found")

        if request.title is not None:
            book.title = request.title
        if request.author is not None:
            book.author = request.author
        if request.genres is not None:
            book.genres = request.genres
        if request.description is not None:
            book.description = request.description
        if request.pages is not None:
            book.pages = request.pages
        if request.isbn is not None:
            book.isbn = request.isbn

        return self._book_repo.update(book)
