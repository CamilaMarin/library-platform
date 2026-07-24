"""Domain unit tests for Library entities (M3 Task 1).

Tests Book/Copy invariants without any database.
Reference: library/design.md Properties 1-3, ADR-0015
"""

from uuid import uuid4

import pytest

from app.library.domain.entities import Book, Copy, CopyStatus, CopyType


class TestBook:
    def test_valid_book_creation(self):
        book = Book(title="Cien años de soledad", author="Gabriel García Márquez")
        assert book.title == "Cien años de soledad"
        assert book.author == "Gabriel García Márquez"
        assert book.genres == []
        assert book.pages is None
        assert book.id is not None

    def test_book_with_full_metadata(self):
        book = Book(
            title="Rayuela",
            author="Julio Cortázar",
            genres=["fiction", "experimental"],
            description="A novel that can be read in multiple orders",
            pages=600,
            isbn="9788437604572",
        )
        assert book.genres == ["fiction", "experimental"]
        assert book.pages == 600
        assert book.isbn == "9788437604572"

    def test_book_requires_title(self):
        with pytest.raises(ValueError, match="title"):
            Book(title="", author="Some Author")

    def test_book_requires_author(self):
        with pytest.raises(ValueError, match="author"):
            Book(title="Some Title", author="")

    def test_book_can_exist_without_copies(self):
        """Property 1: A Book can exist without any associated Copies."""
        book = Book(title="Standalone Book", author="Author")
        assert book.id is not None


class TestCopy:
    def test_valid_physical_copy(self):
        copy = Copy(
            user_id=uuid4(),
            book_id=uuid4(),
            type=CopyType.PHYSICAL,
            file_ref=None,
        )
        assert copy.type == CopyType.PHYSICAL
        assert copy.file_ref is None
        assert copy.status == CopyStatus.AVAILABLE

    def test_valid_digital_copy(self):
        copy = Copy(
            user_id=uuid4(),
            book_id=uuid4(),
            type=CopyType.DIGITAL,
            file_ref="users/abc123/books/mybook.epub",
        )
        assert copy.type == CopyType.DIGITAL
        assert copy.file_ref == "users/abc123/books/mybook.epub"

    def test_physical_copy_cannot_have_file_ref(self):
        """Property 3: physical implies file_ref IS NULL."""
        with pytest.raises(ValueError, match="Physical copy cannot have a file_ref"):
            Copy(
                user_id=uuid4(),
                book_id=uuid4(),
                type=CopyType.PHYSICAL,
                file_ref="some/path.epub",
            )

    def test_digital_copy_requires_file_ref(self):
        with pytest.raises(ValueError, match="Digital copy requires a file_ref"):
            Copy(
                user_id=uuid4(),
                book_id=uuid4(),
                type=CopyType.DIGITAL,
                file_ref=None,
            )

    def test_digital_copy_empty_file_ref_rejected(self):
        with pytest.raises(ValueError, match="Digital copy requires a file_ref"):
            Copy(
                user_id=uuid4(),
                book_id=uuid4(),
                type=CopyType.DIGITAL,
                file_ref="",
            )

    def test_copy_default_status_is_available(self):
        copy = Copy(
            user_id=uuid4(),
            book_id=uuid4(),
            type=CopyType.PHYSICAL,
        )
        assert copy.status == CopyStatus.AVAILABLE
