"""Unit tests for GetReadingProgress use case.

Tests ownership enforcement (403) and None return (no progress yet).
Reference: .kiro/specs/reader/requirements.md Req 2.2, design Property 2
"""

from uuid import uuid4

import pytest

from app.library.application.get_reading_progress import GetReadingProgress
from app.library.domain.entities import (
    Copy,
    CopyType,
    FileFormat,
    ReadingProgress,
)


class FakeCopyRepository:
    """In-memory stub for CopyRepository."""

    def __init__(self, copies: list[Copy] | None = None):
        self._copies = {c.id: c for c in (copies or [])}

    def find_by_id(self, copy_id):
        return self._copies.get(copy_id)

    # Other methods not needed for this use case
    def save(self, copy): ...
    def find_by_user(self, user_id): ...
    def find_by_book(self, book_id): ...
    def update(self, copy): ...
    def delete(self, copy_id): ...


class FakeReadingProgressRepository:
    """In-memory stub for ReadingProgressRepository."""

    def __init__(self, progress_records: list[ReadingProgress] | None = None):
        self._records = progress_records or []

    def find_by_user_and_copy(self, user_id, copy_id):
        for r in self._records:
            if r.user_id == user_id and r.copy_id == copy_id:
                return r
        return None

    # Other methods not needed for this use case
    def upsert(self, progress): ...
    def find_by_user(self, user_id): ...
    def delete_by_copy(self, copy_id): ...


class TestGetReadingProgressOwnership:
    """Tests that ownership is enforced (Property 2)."""

    def test_returns_403_when_user_does_not_own_copy(self):
        owner_id = uuid4()
        requester_id = uuid4()
        copy = Copy(
            user_id=owner_id,
            book_id=uuid4(),
            type=CopyType.DIGITAL,
            file_ref="users/owner/file.pdf",
        )

        use_case = GetReadingProgress(
            copy_repository=FakeCopyRepository([copy]),
            reading_progress_repository=FakeReadingProgressRepository(),
        )

        with pytest.raises(PermissionError, match="do not have access"):
            use_case.execute(copy_id=copy.id, user_id=requester_id)

    def test_raises_value_error_when_copy_not_found(self):
        use_case = GetReadingProgress(
            copy_repository=FakeCopyRepository(),
            reading_progress_repository=FakeReadingProgressRepository(),
        )

        with pytest.raises(ValueError, match="not found"):
            use_case.execute(copy_id=uuid4(), user_id=uuid4())


class TestGetReadingProgressReturnsData:
    """Tests that progress is returned correctly when it exists."""

    def test_returns_progress_when_exists(self):
        user_id = uuid4()
        copy = Copy(
            user_id=user_id,
            book_id=uuid4(),
            type=CopyType.DIGITAL,
            file_ref="users/user/book.pdf",
        )
        progress = ReadingProgress(
            user_id=user_id,
            copy_id=copy.id,
            position="42",
            file_format=FileFormat.PDF,
            percentage=0.5,
        )

        use_case = GetReadingProgress(
            copy_repository=FakeCopyRepository([copy]),
            reading_progress_repository=FakeReadingProgressRepository([progress]),
        )

        result = use_case.execute(copy_id=copy.id, user_id=user_id)

        assert result is not None
        assert result.position == "42"
        assert result.percentage == 0.5
        assert result.file_format == FileFormat.PDF
        assert result.copy_id == copy.id

    def test_returns_none_when_no_progress_saved(self):
        user_id = uuid4()
        copy = Copy(
            user_id=user_id,
            book_id=uuid4(),
            type=CopyType.DIGITAL,
            file_ref="users/user/book.epub",
        )

        use_case = GetReadingProgress(
            copy_repository=FakeCopyRepository([copy]),
            reading_progress_repository=FakeReadingProgressRepository(),
        )

        result = use_case.execute(copy_id=copy.id, user_id=user_id)

        assert result is None
