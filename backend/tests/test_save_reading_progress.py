"""Unit tests for SaveReadingProgress use case (Reader spec, Task 3).

Tests:
- Property 2: Progress isolation — only where progress.user_id == copy.user_id
- Property 3: Idempotent save — same position updates last_read_at, no duplicates
- Error cases: copy not found, physical copy, non-owner

Reference: .kiro/specs/reader/design.md, Requirements 2.1, 2.3
"""

from uuid import UUID, uuid4

import pytest

from app.library.application.save_reading_progress import (
    SaveReadingProgress,
    SaveReadingProgressRequest,
)
from app.library.domain.entities import (
    Copy,
    CopyStatus,
    CopyType,
    FileFormat,
    ReadingProgress,
    ReadingStatus,
    ReadingStatusValue,
)


class FakeCopyRepository:
    """In-memory fake for CopyRepository."""

    def __init__(self, copies: list[Copy] | None = None):
        self._copies = {c.id: c for c in (copies or [])}

    def find_by_id(self, copy_id: UUID) -> Copy | None:
        return self._copies.get(copy_id)


class FakeReadingProgressRepository:
    """In-memory fake for ReadingProgressRepository."""

    def __init__(self):
        self._store: dict[tuple[UUID, UUID], ReadingProgress] = {}

    def upsert(self, progress: ReadingProgress) -> ReadingProgress:
        key = (progress.user_id, progress.copy_id)
        self._store[key] = progress
        return progress

    def find_by_user_and_copy(
        self, user_id: UUID, copy_id: UUID
    ) -> ReadingProgress | None:
        return self._store.get((user_id, copy_id))

    def find_by_user(self, user_id: UUID) -> list[ReadingProgress]:
        return [p for p in self._store.values() if p.user_id == user_id]

    def delete_by_copy(self, copy_id: UUID) -> None:
        keys_to_delete = [k for k, v in self._store.items() if v.copy_id == copy_id]
        for k in keys_to_delete:
            del self._store[k]

    @property
    def count(self) -> int:
        return len(self._store)


def _make_digital_copy(user_id: UUID | None = None) -> Copy:
    """Helper to create a digital copy for testing."""
    uid = user_id or uuid4()
    return Copy(
        id=uuid4(),
        user_id=uid,
        book_id=uuid4(),
        type=CopyType.DIGITAL,
        file_ref="users/{}/books/test.epub".format(uid),
        status=CopyStatus.AVAILABLE,
    )


def _make_physical_copy(user_id: UUID | None = None) -> Copy:
    """Helper to create a physical copy for testing."""
    return Copy(
        id=uuid4(),
        user_id=user_id or uuid4(),
        book_id=uuid4(),
        type=CopyType.PHYSICAL,
        file_ref=None,
        status=CopyStatus.AVAILABLE,
    )


class TestSaveReadingProgressHappyPath:
    """Tests for successful progress save."""

    def test_saves_epub_progress(self):
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        result = use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="epubcfi(/6/4!/4/2/1:0)",
                percentage=0.45,
                file_format=FileFormat.EPUB,
            )
        )

        assert result.user_id == user_id
        assert result.copy_id == copy.id
        assert result.position == "epubcfi(/6/4!/4/2/1:0)"
        assert result.percentage == 0.45
        assert result.file_format == FileFormat.EPUB
        assert progress_repo.count == 1

    def test_saves_pdf_progress(self):
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        result = use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="42",
                percentage=0.7,
                file_format=FileFormat.PDF,
            )
        )

        assert result.position == "42"
        assert result.file_format == FileFormat.PDF


class TestProgressIsolation:
    """Property 2: Progress only where progress.user_id == copy.user_id."""

    def test_rejects_non_owner(self):
        owner_id = uuid4()
        other_user_id = uuid4()
        copy = _make_digital_copy(owner_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        with pytest.raises(ValueError, match="copies owned by the user"):
            use_case.execute(
                SaveReadingProgressRequest(
                    copy_id=copy.id,
                    user_id=other_user_id,
                    position="epubcfi(/6/4!/4/2/1:0)",
                    percentage=0.3,
                    file_format=FileFormat.EPUB,
                )
            )

        assert progress_repo.count == 0


class TestIdempotentSave:
    """Property 3: Same position updates last_read_at, no duplicates."""

    def test_upsert_same_position_no_duplicate(self):
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        request = SaveReadingProgressRequest(
            copy_id=copy.id,
            user_id=user_id,
            position="epubcfi(/6/4!/4/2/1:0)",
            percentage=0.45,
            file_format=FileFormat.EPUB,
        )

        # Save twice
        use_case.execute(request)
        use_case.execute(request)

        # Only one record should exist (upsert behavior)
        assert progress_repo.count == 1


class TestErrorCases:
    """Error scenarios."""

    def test_copy_not_found(self):
        copy_repo = FakeCopyRepository([])
        progress_repo = FakeReadingProgressRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        with pytest.raises(ValueError, match="not found"):
            use_case.execute(
                SaveReadingProgressRequest(
                    copy_id=uuid4(),
                    user_id=uuid4(),
                    position="1",
                    percentage=0.0,
                    file_format=FileFormat.PDF,
                )
            )

    def test_physical_copy_rejected(self):
        user_id = uuid4()
        copy = _make_physical_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        with pytest.raises(ValueError, match="only available for digital copies"):
            use_case.execute(
                SaveReadingProgressRequest(
                    copy_id=copy.id,
                    user_id=user_id,
                    position="1",
                    percentage=0.0,
                    file_format=FileFormat.PDF,
                )
            )

    def test_invalid_epub_position_rejected(self):
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        with pytest.raises(ValueError, match="EPUB position must be a CFI string"):
            use_case.execute(
                SaveReadingProgressRequest(
                    copy_id=copy.id,
                    user_id=user_id,
                    position="not-a-cfi",
                    percentage=0.5,
                    file_format=FileFormat.EPUB,
                )
            )


# --- Tests for ReadingStatus sync (library preview bar) ---


class FakeReadingStatusRepository:
    """In-memory fake for ReadingStatusRepository."""

    def __init__(self):
        self._store: dict[tuple[UUID, UUID], "ReadingStatus"] = {}

    def upsert(self, reading_status: "ReadingStatus") -> "ReadingStatus":
        key = (reading_status.user_id, reading_status.book_id)
        self._store[key] = reading_status
        return reading_status

    def find_by_user(self, user_id: UUID) -> list["ReadingStatus"]:
        return [s for s in self._store.values() if s.user_id == user_id]

    def find_by_user_and_book(
        self, user_id: UUID, book_id: UUID
    ) -> "ReadingStatus | None":
        return self._store.get((user_id, book_id))

    def delete(self, user_id: UUID, book_id: UUID) -> None:
        self._store.pop((user_id, book_id), None)


class TestReadingStatusSync:
    """Tests that saving PDF progress syncs ReadingStatus.current_page."""

    def test_pdf_progress_updates_reading_status_current_page(self):
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        status_repo = FakeReadingStatusRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
            reading_status_repository=status_repo,
        )

        use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="42",
                percentage=0.7,
                file_format=FileFormat.PDF,
            )
        )

        status = status_repo.find_by_user_and_book(user_id, copy.book_id)
        assert status is not None
        assert status.current_page == 42
        assert status.status == ReadingStatusValue.READING

    def test_epub_progress_does_not_sync_without_book_repo(self):
        """EPUB progress doesn't sync when book_repository is None."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        status_repo = FakeReadingStatusRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
            reading_status_repository=status_repo,
            book_repository=None,
        )

        use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="epubcfi(/6/4!/4/2/1:0)",
                percentage=0.5,
                file_format=FileFormat.EPUB,
            )
        )

        status = status_repo.find_by_user_and_book(user_id, copy.book_id)
        assert status is None

    def test_epub_progress_syncs_when_book_has_pages(self):
        """EPUB progress syncs current_page using percentage × book.pages."""
        from app.library.domain.entities import Book

        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        status_repo = FakeReadingStatusRepository()

        class FakeBookRepo:
            def __init__(self, book):
                self._book = book

            def find_by_id(self, book_id):
                return self._book if self._book.id == book_id else None

            def save(self, book): ...
            def find_by_user_copies(self, user_id): ...
            def find_by_group_members(self, member_ids): ...
            def search(self, query, user_id, group_member_ids=None): ...
            def update(self, book): ...
            def delete(self, book_id): ...
            def has_copies(self, book_id): ...

        book = Book(id=copy.book_id, title="Test EPUB", author="Author", pages=300)
        book_repo = FakeBookRepo(book)

        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
            reading_status_repository=status_repo,
            book_repository=book_repo,
        )

        use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="epubcfi(/6/4!/4/2/1:0)",
                percentage=0.5,
                file_format=FileFormat.EPUB,
            )
        )

        status = status_repo.find_by_user_and_book(user_id, copy.book_id)
        assert status is not None
        assert status.current_page == 150  # 0.5 × 300
        assert status.status == ReadingStatusValue.READING

    def test_epub_progress_no_sync_when_book_has_no_pages(self):
        """EPUB progress doesn't sync when book.pages is None."""
        from app.library.domain.entities import Book

        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        status_repo = FakeReadingStatusRepository()

        class FakeBookRepo:
            def __init__(self, book):
                self._book = book

            def find_by_id(self, book_id):
                return self._book if self._book.id == book_id else None

            def save(self, book): ...
            def find_by_user_copies(self, user_id): ...
            def find_by_group_members(self, member_ids): ...
            def search(self, query, user_id, group_member_ids=None): ...
            def update(self, book): ...
            def delete(self, book_id): ...
            def has_copies(self, book_id): ...

        book = Book(id=copy.book_id, title="Test EPUB", author="Author", pages=None)
        book_repo = FakeBookRepo(book)

        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
            reading_status_repository=status_repo,
            book_repository=book_repo,
        )

        use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="epubcfi(/6/4!/4/2/1:0)",
                percentage=0.5,
                file_format=FileFormat.EPUB,
            )
        )

        status = status_repo.find_by_user_and_book(user_id, copy.book_id)
        assert status is None  # No sync because book has no page count

    def test_does_not_override_read_status(self):
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        status_repo = FakeReadingStatusRepository()

        # Pre-set the status to "read"
        existing_status = ReadingStatus(
            user_id=user_id,
            book_id=copy.book_id,
            status=ReadingStatusValue.READ,
            current_page=200,
        )
        status_repo.upsert(existing_status)

        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
            reading_status_repository=status_repo,
        )

        use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="50",
                percentage=0.3,
                file_format=FileFormat.PDF,
            )
        )

        status = status_repo.find_by_user_and_book(user_id, copy.book_id)
        assert status.status == ReadingStatusValue.READ
        assert status.current_page == 200  # Unchanged

    def test_does_not_override_dnf_status(self):
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        status_repo = FakeReadingStatusRepository()

        existing_status = ReadingStatus(
            user_id=user_id,
            book_id=copy.book_id,
            status=ReadingStatusValue.DNF,
            current_page=100,
        )
        status_repo.upsert(existing_status)

        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
            reading_status_repository=status_repo,
        )

        use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="50",
                percentage=0.3,
                file_format=FileFormat.PDF,
            )
        )

        status = status_repo.find_by_user_and_book(user_id, copy.book_id)
        assert status.status == ReadingStatusValue.DNF
        assert status.current_page == 100  # Unchanged

    def test_updates_existing_reading_status(self):
        """When status is already 'reading', update the current_page."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        status_repo = FakeReadingStatusRepository()

        existing_status = ReadingStatus(
            user_id=user_id,
            book_id=copy.book_id,
            status=ReadingStatusValue.READING,
            current_page=10,
        )
        status_repo.upsert(existing_status)

        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
            reading_status_repository=status_repo,
        )

        use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="75",
                percentage=0.5,
                file_format=FileFormat.PDF,
            )
        )

        status = status_repo.find_by_user_and_book(user_id, copy.book_id)
        assert status.current_page == 75
        assert status.status == ReadingStatusValue.READING

    def test_no_status_repo_provided_skips_sync(self):
        """When reading_status_repository is None, sync is skipped gracefully."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id)
        copy_repo = FakeCopyRepository([copy])
        progress_repo = FakeReadingProgressRepository()
        use_case = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
            reading_status_repository=None,
        )

        # Should not raise
        result = use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="42",
                percentage=0.7,
                file_format=FileFormat.PDF,
            )
        )

        assert result.position == "42"
