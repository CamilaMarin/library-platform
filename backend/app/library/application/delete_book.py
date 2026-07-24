"""DeleteBook use case.

Deletes a book. Rejects with 409 if copies still exist.
Reference: library/requirements.md Req 1.5, library/design.md Error Handling
"""

from uuid import UUID

from app.library.application.protocols import BookRepository


class BookHasCopiesError(Exception):
    """Raised when attempting to delete a book that still has copies."""

    pass


class DeleteBook:
    """Use case: delete a book.

    Returns 409 conflict if the book has any associated copies.
    User must delete copies first.
    """

    def __init__(self, book_repository: BookRepository):
        self._book_repo = book_repository

    def execute(self, book_id: UUID) -> None:
        """Delete a book by ID. Raises BookHasCopiesError if copies exist."""
        book = self._book_repo.find_by_id(book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")

        if self._book_repo.has_copies(book_id):
            raise BookHasCopiesError(
                f"Cannot delete book {book_id}: copies still exist. Delete copies first."
            )

        self._book_repo.delete(book_id)
