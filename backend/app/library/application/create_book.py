"""CreateBook use case.

Creates a Book (metadata only, no copies). Books are standalone catalog entities.
Reference: library/requirements.md Req 1.1, ADR-0015
"""

from dataclasses import dataclass
from uuid import UUID

from app.library.application.protocols import BookRepository
from app.library.domain.entities import Book


@dataclass
class CreateBookRequest:
    """Input for CreateBook use case."""

    title: str
    author: str
    genres: list[str] | None = None
    description: str = ""
    pages: int | None = None
    isbn: str | None = None


class CreateBook:
    """Use case: create a book (metadata only).

    Books exist independently of copies (ADR-0015 Property 1).
    Any authenticated user can create a book.
    """

    def __init__(self, book_repository: BookRepository):
        self._book_repo = book_repository

    def execute(self, request: CreateBookRequest, user_id: UUID) -> Book:
        """Create and persist a new Book."""
        book = Book(
            title=request.title,
            author=request.author,
            genres=request.genres or [],
            description=request.description,
            pages=request.pages,
            isbn=request.isbn,
        )
        return self._book_repo.save(book)
