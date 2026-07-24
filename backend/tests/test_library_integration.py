"""Integration tests for Library module (M3 Task 7).

Tests: CreateBook, CreateCopy, Edit/Delete, Search, ownership enforcement,
file_ref isolation, DeleteBook 409.

Reference: library/design.md Properties 1-5, ADR-0001, ADR-0009, ADR-0015
"""

from uuid import uuid4

import pytest

from app.library.application.create_book import CreateBook, CreateBookRequest
from app.library.application.create_copy import (
    CreateCopy,
    CreateDigitalCopyRequest,
    CreatePhysicalCopyRequest,
)
from app.library.application.delete_book import BookHasCopiesError, DeleteBook
from app.library.application.delete_copy import DeleteCopy
from app.library.application.search_books import SearchBooks
from app.library.domain.entities import Book, Copy, CopyType

# --- In-memory test doubles ---


class InMemoryBookRepository:
    def __init__(self):
        self.books: dict = {}
        self.copies_by_book: dict = {}

    def save(self, book: Book) -> Book:
        self.books[book.id] = book
        return book

    def find_by_id(self, book_id):
        return self.books.get(book_id)

    def find_by_user_copies(self, user_id):
        return [
            self.books[bid]
            for bid, copies in self.copies_by_book.items()
            if any(c.user_id == user_id for c in copies)
            if bid in self.books
        ]

    def find_by_group_members(self, member_ids):
        result = []
        for bid, copies in self.copies_by_book.items():
            if any(c.user_id in member_ids for c in copies) and bid in self.books:
                result.append(self.books[bid])
        return result

    def search(self, query, user_id, group_member_ids=None):
        owner_ids = [user_id]
        if group_member_ids:
            owner_ids.extend(group_member_ids)
        results = []
        for bid, copies in self.copies_by_book.items():
            if any(c.user_id in owner_ids for c in copies) and bid in self.books:
                book = self.books[bid]
                q = query.lower()
                if q in book.title.lower() or q in book.author.lower():
                    results.append(book)
        return results

    def update(self, book: Book) -> Book:
        self.books[book.id] = book
        return book

    def delete(self, book_id):
        self.books.pop(book_id, None)

    def has_copies(self, book_id):
        return bool(self.copies_by_book.get(book_id))

    def register_copy(self, copy: Copy):
        self.copies_by_book.setdefault(copy.book_id, []).append(copy)

    def remove_copy(self, copy: Copy):
        copies = self.copies_by_book.get(copy.book_id, [])
        self.copies_by_book[copy.book_id] = [c for c in copies if c.id != copy.id]


class InMemoryCopyRepository:
    def __init__(self, book_repo: InMemoryBookRepository):
        self.copies: dict = {}
        self._book_repo = book_repo

    def save(self, copy: Copy) -> Copy:
        self.copies[copy.id] = copy
        self._book_repo.register_copy(copy)
        return copy

    def find_by_id(self, copy_id):
        return self.copies.get(copy_id)

    def find_by_user(self, user_id):
        return [c for c in self.copies.values() if c.user_id == user_id]

    def find_by_book(self, book_id):
        return [c for c in self.copies.values() if c.book_id == book_id]

    def update(self, copy: Copy) -> Copy:
        self.copies[copy.id] = copy
        return copy

    def delete(self, copy_id):
        copy = self.copies.pop(copy_id, None)
        if copy:
            self._book_repo.remove_copy(copy)


class InMemoryFileStorage:
    def __init__(self):
        self.files: dict = {}

    def upload(self, user_id, filename, content) -> str:
        ref = f"users/{user_id}/{filename}"
        self.files[ref] = content
        return ref

    def download(self, file_ref) -> bytes:
        if file_ref not in self.files:
            raise FileNotFoundError(file_ref)
        return self.files[file_ref]

    def delete(self, file_ref):
        self.files.pop(file_ref, None)


# --- Tests ---


class TestCreateBook:
    def test_creates_book_successfully(self):
        repo = InMemoryBookRepository()
        uc = CreateBook(book_repository=repo)
        book = uc.execute(
            CreateBookRequest(title="Test Book", author="Author"), user_id=uuid4()
        )
        assert book.title == "Test Book"
        assert repo.find_by_id(book.id) is not None

    def test_book_exists_without_copies(self):
        """Property 1: Book can exist without copies."""
        repo = InMemoryBookRepository()
        uc = CreateBook(book_repository=repo)
        book = uc.execute(
            CreateBookRequest(title="Standalone", author="Author"), user_id=uuid4()
        )
        assert not repo.has_copies(book.id)


class TestCreateCopy:
    def test_create_physical_copy(self):
        book_repo = InMemoryBookRepository()
        copy_repo = InMemoryCopyRepository(book_repo)
        book = Book(title="Test", author="Author")
        book_repo.save(book)

        uc = CreateCopy(copy_repository=copy_repo, book_repository=book_repo)
        copy = uc.create_physical(
            CreatePhysicalCopyRequest(book_id=book.id, user_id=uuid4())
        )
        assert copy.type == CopyType.PHYSICAL
        assert copy.file_ref is None

    def test_create_digital_copy(self):
        book_repo = InMemoryBookRepository()
        copy_repo = InMemoryCopyRepository(book_repo)
        file_storage = InMemoryFileStorage()
        book = Book(title="Test", author="Author")
        book_repo.save(book)
        user_id = uuid4()

        uc = CreateCopy(
            copy_repository=copy_repo,
            book_repository=book_repo,
            file_storage=file_storage,
        )
        copy = uc.create_digital(
            CreateDigitalCopyRequest(
                book_id=book.id,
                user_id=user_id,
                filename="book.epub",
                content=b"fake epub content",
            )
        )
        assert copy.type == CopyType.DIGITAL
        assert copy.file_ref == f"users/{user_id}/book.epub"
        assert file_storage.files[copy.file_ref] == b"fake epub content"

    def test_rejects_unsupported_format(self):
        book_repo = InMemoryBookRepository()
        copy_repo = InMemoryCopyRepository(book_repo)
        file_storage = InMemoryFileStorage()
        book = Book(title="Test", author="Author")
        book_repo.save(book)

        uc = CreateCopy(
            copy_repository=copy_repo,
            book_repository=book_repo,
            file_storage=file_storage,
        )
        with pytest.raises(ValueError, match="Unsupported file format"):
            uc.create_digital(
                CreateDigitalCopyRequest(
                    book_id=book.id,
                    user_id=uuid4(),
                    filename="book.txt",
                    content=b"text content",
                )
            )

    def test_rejects_nonexistent_book(self):
        book_repo = InMemoryBookRepository()
        copy_repo = InMemoryCopyRepository(book_repo)

        uc = CreateCopy(copy_repository=copy_repo, book_repository=book_repo)
        with pytest.raises(ValueError, match="not found"):
            uc.create_physical(
                CreatePhysicalCopyRequest(book_id=uuid4(), user_id=uuid4())
            )


class TestDeleteBook:
    def test_delete_book_without_copies(self):
        repo = InMemoryBookRepository()
        book = Book(title="Deletable", author="Author")
        repo.save(book)

        uc = DeleteBook(book_repository=repo)
        uc.execute(book.id)
        assert repo.find_by_id(book.id) is None

    def test_delete_book_with_copies_raises_409(self):
        """DeleteBook rejects with 409 when copies exist."""
        book_repo = InMemoryBookRepository()
        copy_repo = InMemoryCopyRepository(book_repo)
        book = Book(title="Has Copies", author="Author")
        book_repo.save(book)
        copy = Copy(
            user_id=uuid4(),
            book_id=book.id,
            type=CopyType.PHYSICAL,
        )
        copy_repo.save(copy)

        uc = DeleteBook(book_repository=book_repo)
        with pytest.raises(BookHasCopiesError):
            uc.execute(book.id)


class TestDeleteCopy:
    def test_owner_can_delete_copy(self):
        book_repo = InMemoryBookRepository()
        copy_repo = InMemoryCopyRepository(book_repo)
        user_id = uuid4()
        copy = Copy(user_id=user_id, book_id=uuid4(), type=CopyType.PHYSICAL)
        copy_repo.copies[copy.id] = copy

        uc = DeleteCopy(copy_repository=copy_repo)
        uc.execute(copy_id=copy.id, user_id=user_id)
        assert copy_repo.find_by_id(copy.id) is None

    def test_non_owner_cannot_delete(self):
        """Ownership enforcement: non-owner gets PermissionError."""
        book_repo = InMemoryBookRepository()
        copy_repo = InMemoryCopyRepository(book_repo)
        copy = Copy(user_id=uuid4(), book_id=uuid4(), type=CopyType.PHYSICAL)
        copy_repo.copies[copy.id] = copy

        uc = DeleteCopy(copy_repository=copy_repo)
        with pytest.raises(PermissionError):
            uc.execute(copy_id=copy.id, user_id=uuid4())

    def test_digital_copy_deletion_removes_file(self):
        """ADR-0009: digital file removed from storage on copy deletion."""
        book_repo = InMemoryBookRepository()
        copy_repo = InMemoryCopyRepository(book_repo)
        file_storage = InMemoryFileStorage()
        user_id = uuid4()
        file_ref = f"users/{user_id}/book.pdf"
        file_storage.files[file_ref] = b"pdf content"

        copy = Copy(
            user_id=user_id,
            book_id=uuid4(),
            type=CopyType.DIGITAL,
            file_ref=file_ref,
        )
        copy_repo.copies[copy.id] = copy

        uc = DeleteCopy(copy_repository=copy_repo, file_storage=file_storage)
        uc.execute(copy_id=copy.id, user_id=user_id)
        assert file_ref not in file_storage.files


class TestSearchBooks:
    def test_search_finds_matching_books(self):
        book_repo = InMemoryBookRepository()
        user_id = uuid4()
        book = Book(title="Cien años de soledad", author="García Márquez")
        book_repo.save(book)
        copy = Copy(user_id=user_id, book_id=book.id, type=CopyType.PHYSICAL)
        book_repo.register_copy(copy)

        uc = SearchBooks(book_repository=book_repo)
        results = uc.execute(query="soledad", user_id=user_id)
        assert len(results) == 1
        assert results[0].title == "Cien años de soledad"

    def test_search_empty_query_returns_empty(self):
        book_repo = InMemoryBookRepository()
        uc = SearchBooks(book_repository=book_repo)
        assert uc.execute(query="", user_id=uuid4()) == []

    def test_search_no_match_returns_empty(self):
        book_repo = InMemoryBookRepository()
        user_id = uuid4()
        book = Book(title="Rayuela", author="Cortázar")
        book_repo.save(book)
        copy = Copy(user_id=user_id, book_id=book.id, type=CopyType.PHYSICAL)
        book_repo.register_copy(copy)

        uc = SearchBooks(book_repository=book_repo)
        assert uc.execute(query="nonexistent", user_id=user_id) == []

    def test_search_only_finds_user_or_group_books(self):
        """Property 5: Search only returns books from accessible libraries."""
        book_repo = InMemoryBookRepository()
        user_a = uuid4()
        user_b = uuid4()
        user_c = uuid4()  # not in group

        book_a = Book(title="Book A", author="Author")
        book_c = Book(title="Book C", author="Author")
        book_repo.save(book_a)
        book_repo.save(book_c)
        book_repo.register_copy(
            Copy(user_id=user_a, book_id=book_a.id, type=CopyType.PHYSICAL)
        )
        book_repo.register_copy(
            Copy(user_id=user_c, book_id=book_c.id, type=CopyType.PHYSICAL)
        )

        uc = SearchBooks(book_repository=book_repo)
        # user_a searches with group [user_b] — should NOT find book_c
        results = uc.execute(query="Book", user_id=user_a, group_member_ids=[user_b])
        assert len(results) == 1
        assert results[0].id == book_a.id
