"""CreateBook use case.

Creates a Book (metadata only, no copies). Books are standalone catalog entities.
Reference: library/requirements.md Req 1.1, ADR-0015
"""

from dataclasses import dataclass
from uuid import UUID

from app.library.application.protocols import BookRepository, CopyRepository
from app.library.domain.entities import Book, Copy, CopyType


@dataclass
class CreateBookRequest:
    """Input for CreateBook use case."""

    title: str
    author: str
    genres: list[str] | None = None
    description: str = ""
    pages: int | None = None
    isbn: str | None = None
    initial_copy_format: str | None = None


class CreateBook:
    """Use case: create a book (metadata only).

    Books exist independently of copies (ADR-0015 Property 1).
    Any authenticated user can create a book.
    """

    def __init__(self, book_repository: BookRepository, copy_repository: CopyRepository | None = None):
        self._book_repo = book_repository
        self._copy_repo = copy_repository

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
        book = self._book_repo.save(book)

        if request.initial_copy_format and self._copy_repo:
            if request.initial_copy_format == "physical":
                copy = Copy(
                    user_id=user_id,
                    book_id=book.id,
                    type=CopyType.PHYSICAL,
                )
                self._copy_repo.save(copy)

        return book
