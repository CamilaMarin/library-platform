"""Integration + security tests for Reader module (Task 7).

Tests: ownership enforcement, progress isolation, no file_ref leakage.
Pure application-layer tests — no DB, no HTTP. Uses in-memory test doubles.

Reference: reader/design.md Properties 1-4, reader/requirements.md Req 1-3
Reference: ADR-0001, ADR-0009, ADR-0014
"""

from uuid import uuid4

import pytest

from app.library.application.get_reading_progress import GetReadingProgress
from app.library.application.open_reader import OpenReader
from app.library.application.save_reading_progress import (
    SaveReadingProgress,
    SaveReadingProgressRequest,
)
from app.library.domain.entities import (
    Copy,
    CopyType,
    FileFormat,
    ReadingProgress,
)

# --- In-memory test doubles ---


class InMemoryCopyRepository:
    """Test double for CopyRepository protocol."""

    def __init__(self):
        self.copies: dict = {}

    def save(self, copy: Copy) -> Copy:
        self.copies[copy.id] = copy
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
        self.copies.pop(copy_id, None)


class InMemoryFileStorage:
    """Test double for FileStorage protocol."""

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


class InMemoryReadingProgressRepository:
    """Test double for ReadingProgressRepository protocol."""

    def __init__(self):
        self.records: dict = {}  # key: (user_id, copy_id)

    def upsert(self, progress: ReadingProgress) -> ReadingProgress:
        self.records[(progress.user_id, progress.copy_id)] = progress
        return progress

    def find_by_user_and_copy(self, user_id, copy_id) -> ReadingProgress | None:
        return self.records.get((user_id, copy_id))

    def find_by_user(self, user_id) -> list[ReadingProgress]:
        return [p for p in self.records.values() if p.user_id == user_id]

    def delete_by_copy(self, copy_id):
        keys_to_remove = [k for k in self.records if k[1] == copy_id]
        for key in keys_to_remove:
            del self.records[key]


# --- Fixtures ---


@pytest.fixture
def copy_repo():
    return InMemoryCopyRepository()


@pytest.fixture
def file_storage():
    return InMemoryFileStorage()


@pytest.fixture
def progress_repo():
    return InMemoryReadingProgressRepository()


def _make_digital_copy(user_id, file_storage, copy_repo, filename="book.epub"):
    """Helper: create a digital copy owned by user_id with a file in storage."""
    file_ref = file_storage.upload(user_id, filename, b"fake file content")
    copy = Copy(
        user_id=user_id,
        book_id=uuid4(),
        type=CopyType.DIGITAL,
        file_ref=file_ref,
    )
    copy_repo.save(copy)
    return copy


def _make_physical_copy(user_id, copy_repo):
    """Helper: create a physical copy owned by user_id."""
    copy = Copy(
        user_id=user_id,
        book_id=uuid4(),
        type=CopyType.PHYSICAL,
    )
    copy_repo.save(copy)
    return copy


# --- Tests: OpenReader Ownership (Property 1) ---


class TestOpenReaderOwnership:
    """Property 1: Ownership gate — file served ONLY to owner."""

    def test_owner_can_download_file(self, copy_repo, file_storage):
        """Owner gets 200 with file content."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo)

        uc = OpenReader(copy_repository=copy_repo, file_storage=file_storage)
        content = uc.execute(copy_id=copy.id, request_user_id=user_id)

        assert content == b"fake file content"

    def test_non_owner_gets_permission_error(self, copy_repo, file_storage):
        """Non-owner gets 403 (PermissionError) — never 404."""
        owner_id = uuid4()
        other_user_id = uuid4()
        copy = _make_digital_copy(owner_id, file_storage, copy_repo)

        uc = OpenReader(copy_repository=copy_repo, file_storage=file_storage)

        with pytest.raises(PermissionError, match="Access denied"):
            uc.execute(copy_id=copy.id, request_user_id=other_user_id)

    def test_nonexistent_copy_gets_permission_error(self, copy_repo, file_storage):
        """Non-existent copy ID returns 403 (same as non-owner) — never leaks existence."""
        uc = OpenReader(copy_repository=copy_repo, file_storage=file_storage)

        with pytest.raises(PermissionError, match="Access denied"):
            uc.execute(copy_id=uuid4(), request_user_id=uuid4())

    def test_physical_copy_raises_value_error(self, copy_repo, file_storage):
        """Physical copy has no file → ValueError (422)."""
        user_id = uuid4()
        copy = _make_physical_copy(user_id, copy_repo)

        uc = OpenReader(copy_repository=copy_repo, file_storage=file_storage)

        with pytest.raises(ValueError, match="physical copy"):
            uc.execute(copy_id=copy.id, request_user_id=user_id)

    def test_file_missing_from_storage_raises_file_not_found(
        self, copy_repo, file_storage
    ):
        """File missing from storage → FileNotFoundError."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo)

        # Remove the file from storage (simulating corruption/deletion)
        file_storage.delete(copy.file_ref)

        uc = OpenReader(copy_repository=copy_repo, file_storage=file_storage)

        with pytest.raises(FileNotFoundError):
            uc.execute(copy_id=copy.id, request_user_id=user_id)


# --- Tests: SaveReadingProgress (Property 2: Isolation + Property 3: Idempotent) ---


class TestSaveReadingProgressIsolation:
    """Property 2: Progress isolation + Property 3: Idempotent save."""

    def test_owner_can_save_progress(self, copy_repo, file_storage, progress_repo):
        """Owner saves progress for their digital copy → success."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo)

        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        request = SaveReadingProgressRequest(
            copy_id=copy.id,
            user_id=user_id,
            position="epubcfi(/6/4!/4/2/1:0)",
            percentage=0.25,
            file_format=FileFormat.EPUB,
        )
        progress = uc.execute(request)

        assert progress.user_id == user_id
        assert progress.copy_id == copy.id
        assert progress.position == "epubcfi(/6/4!/4/2/1:0)"
        assert progress.percentage == 0.25

    def test_non_owner_cannot_save_progress(
        self, copy_repo, file_storage, progress_repo
    ):
        """Non-owner cannot save progress for someone else's copy → ValueError."""
        owner_id = uuid4()
        other_user_id = uuid4()
        copy = _make_digital_copy(owner_id, file_storage, copy_repo)

        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        request = SaveReadingProgressRequest(
            copy_id=copy.id,
            user_id=other_user_id,
            position="epubcfi(/6/4!/4/2/1:0)",
            percentage=0.1,
            file_format=FileFormat.EPUB,
        )

        with pytest.raises(ValueError, match="owned by the user"):
            uc.execute(request)

    def test_cannot_save_progress_for_physical_copy(
        self, copy_repo, file_storage, progress_repo
    ):
        """Cannot save progress for physical copy → ValueError."""
        user_id = uuid4()
        copy = _make_physical_copy(user_id, copy_repo)

        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        request = SaveReadingProgressRequest(
            copy_id=copy.id,
            user_id=user_id,
            position="42",
            percentage=0.5,
            file_format=FileFormat.PDF,
        )

        with pytest.raises(ValueError, match="digital copies"):
            uc.execute(request)

    def test_invalid_epub_position_raises_value_error(
        self, copy_repo, file_storage, progress_repo
    ):
        """Invalid position format (non-CFI for EPUB) → ValueError from entity."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo)

        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        request = SaveReadingProgressRequest(
            copy_id=copy.id,
            user_id=user_id,
            position="page 42",  # Invalid — not a CFI string
            percentage=0.5,
            file_format=FileFormat.EPUB,
        )

        with pytest.raises(ValueError, match="CFI"):
            uc.execute(request)

    def test_duplicate_save_is_idempotent(
        self, copy_repo, file_storage, progress_repo
    ):
        """Property 3: Same position is idempotent — updates last_read_at, no duplicates."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo, filename="book.pdf")

        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        request = SaveReadingProgressRequest(
            copy_id=copy.id,
            user_id=user_id,
            position="10",
            percentage=0.3,
            file_format=FileFormat.PDF,
        )

        # First save
        uc.execute(request)

        # Second save with same position — idempotent
        uc.execute(request)

        # Should still only have one record for this user+copy
        assert progress_repo.find_by_user_and_copy(user_id, copy.id) is not None
        assert len([p for p in progress_repo.records.values()
                    if p.user_id == user_id and p.copy_id == copy.id]) == 1

    def test_percentage_out_of_range_raises_value_error(
        self, copy_repo, file_storage, progress_repo
    ):
        """Percentage > 1.0 or < 0.0 → ValueError."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo, filename="book.pdf")

        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        with pytest.raises(ValueError, match="[Pp]ercentage"):
            uc.execute(
                SaveReadingProgressRequest(
                    copy_id=copy.id,
                    user_id=user_id,
                    position="5",
                    percentage=1.5,
                    file_format=FileFormat.PDF,
                )
            )

        with pytest.raises(ValueError, match="[Pp]ercentage"):
            uc.execute(
                SaveReadingProgressRequest(
                    copy_id=copy.id,
                    user_id=user_id,
                    position="5",
                    percentage=-0.1,
                    file_format=FileFormat.PDF,
                )
            )

    def test_nonexistent_copy_raises_value_error(
        self, copy_repo, file_storage, progress_repo
    ):
        """Non-existent copy → ValueError."""
        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        request = SaveReadingProgressRequest(
            copy_id=uuid4(),
            user_id=uuid4(),
            position="epubcfi(/6/4!/4/2/1:0)",
            percentage=0.1,
            file_format=FileFormat.EPUB,
        )

        with pytest.raises(ValueError, match="not found"):
            uc.execute(request)


# --- Tests: GetReadingProgress (Property 2: Isolation) ---


class TestGetReadingProgressIsolation:
    """Property 2: Progress can only be read by the copy owner."""

    def test_owner_can_retrieve_progress(
        self, copy_repo, file_storage, progress_repo
    ):
        """Owner retrieves their progress → returns data."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo)

        # Save some progress first
        progress = ReadingProgress(
            user_id=user_id,
            copy_id=copy.id,
            position="epubcfi(/6/4!/4/2/1:0)",
            file_format=FileFormat.EPUB,
            percentage=0.5,
        )
        progress_repo.upsert(progress)

        uc = GetReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        result = uc.execute(copy_id=copy.id, user_id=user_id)

        assert result is not None
        assert result.position == "epubcfi(/6/4!/4/2/1:0)"
        assert result.percentage == 0.5

    def test_non_owner_cannot_retrieve_progress(
        self, copy_repo, file_storage, progress_repo
    ):
        """Non-owner cannot retrieve progress → PermissionError."""
        owner_id = uuid4()
        other_user_id = uuid4()
        copy = _make_digital_copy(owner_id, file_storage, copy_repo)

        uc = GetReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        with pytest.raises(PermissionError):
            uc.execute(copy_id=copy.id, user_id=other_user_id)

    def test_no_progress_saved_returns_none(
        self, copy_repo, file_storage, progress_repo
    ):
        """No progress saved yet → returns None (owner still has access)."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo)

        uc = GetReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        result = uc.execute(copy_id=copy.id, user_id=user_id)

        assert result is None

    def test_nonexistent_copy_raises_value_error(
        self, copy_repo, file_storage, progress_repo
    ):
        """Non-existent copy → ValueError."""
        uc = GetReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        with pytest.raises(ValueError, match="not found"):
            uc.execute(copy_id=uuid4(), user_id=uuid4())


# --- Tests: Cross-user Isolation ---


class TestCrossUserIsolation:
    """Security: verify strict isolation between users across all use cases."""

    def test_user_b_cannot_access_user_a_file(
        self, copy_repo, file_storage, progress_repo
    ):
        """User A creates digital copy → User B cannot access file."""
        user_a = uuid4()
        user_b = uuid4()
        copy = _make_digital_copy(user_a, file_storage, copy_repo)

        uc = OpenReader(copy_repository=copy_repo, file_storage=file_storage)

        with pytest.raises(PermissionError, match="Access denied"):
            uc.execute(copy_id=copy.id, request_user_id=user_b)

    def test_user_b_cannot_read_user_a_progress(
        self, copy_repo, file_storage, progress_repo
    ):
        """User A saves progress → User B cannot read it."""
        user_a = uuid4()
        user_b = uuid4()
        copy = _make_digital_copy(user_a, file_storage, copy_repo)

        # User A saves progress
        progress = ReadingProgress(
            user_id=user_a,
            copy_id=copy.id,
            position="epubcfi(/6/4!/4/2/1:0)",
            file_format=FileFormat.EPUB,
            percentage=0.7,
        )
        progress_repo.upsert(progress)

        # User B tries to read it
        uc = GetReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        with pytest.raises(PermissionError):
            uc.execute(copy_id=copy.id, user_id=user_b)

    def test_user_b_cannot_save_progress_on_user_a_copy(
        self, copy_repo, file_storage, progress_repo
    ):
        """User B saving progress on User A's copy → rejected."""
        user_a = uuid4()
        user_b = uuid4()
        copy = _make_digital_copy(user_a, file_storage, copy_repo)

        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        request = SaveReadingProgressRequest(
            copy_id=copy.id,
            user_id=user_b,
            position="epubcfi(/6/4!/4/2/1:0)",
            percentage=0.1,
            file_format=FileFormat.EPUB,
        )

        with pytest.raises(ValueError, match="owned by the user"):
            uc.execute(request)

    def test_two_users_independent_progress(
        self, copy_repo, file_storage, progress_repo
    ):
        """Each user has independent progress on their own copies."""
        user_a = uuid4()
        user_b = uuid4()
        copy_a = _make_digital_copy(user_a, file_storage, copy_repo, "book_a.epub")
        copy_b = _make_digital_copy(user_b, file_storage, copy_repo, "book_b.epub")

        uc_save = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        # User A saves progress on their copy
        uc_save.execute(
            SaveReadingProgressRequest(
                copy_id=copy_a.id,
                user_id=user_a,
                position="epubcfi(/6/4!/4/2/1:0)",
                percentage=0.3,
                file_format=FileFormat.EPUB,
            )
        )

        # User B saves progress on their copy
        uc_save.execute(
            SaveReadingProgressRequest(
                copy_id=copy_b.id,
                user_id=user_b,
                position="epubcfi(/6/8!/4/2/1:0)",
                percentage=0.6,
                file_format=FileFormat.EPUB,
            )
        )

        uc_get = GetReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )

        # Each user sees only their own progress
        progress_a = uc_get.execute(copy_id=copy_a.id, user_id=user_a)
        progress_b = uc_get.execute(copy_id=copy_b.id, user_id=user_b)

        assert progress_a.percentage == 0.3
        assert progress_b.percentage == 0.6

        # Cross-access is denied
        with pytest.raises(PermissionError):
            uc_get.execute(copy_id=copy_a.id, user_id=user_b)

        with pytest.raises(PermissionError):
            uc_get.execute(copy_id=copy_b.id, user_id=user_a)


# --- Tests: No file_ref Leakage ---


class TestNoFileRefLeakage:
    """Security: verify file_ref is never exposed in use case responses.

    The ReadingProgress entity and use case responses should NEVER contain
    the underlying file path (file_ref). Only the OpenReader use case returns
    file content bytes — it never returns the file_ref string itself.
    """

    def test_open_reader_returns_content_not_file_ref(
        self, copy_repo, file_storage
    ):
        """OpenReader returns bytes content, not the file_ref path."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo)

        uc = OpenReader(copy_repository=copy_repo, file_storage=file_storage)
        result = uc.execute(copy_id=copy.id, request_user_id=user_id)

        # Result is raw bytes, not a file path string
        assert isinstance(result, bytes)
        assert result == b"fake file content"
        # The file_ref itself is never in the response
        assert copy.file_ref.encode() not in result

    def test_save_progress_response_has_no_file_ref(
        self, copy_repo, file_storage, progress_repo
    ):
        """SaveReadingProgress response (ReadingProgress) has no file_ref attribute."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo, "book.pdf")

        uc = SaveReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        progress = uc.execute(
            SaveReadingProgressRequest(
                copy_id=copy.id,
                user_id=user_id,
                position="10",
                percentage=0.3,
                file_format=FileFormat.PDF,
            )
        )

        # ReadingProgress entity should not have file_ref
        assert not hasattr(progress, "file_ref")
        # Verify via __dict__ that no field contains the file path
        for value in progress.__dict__.values():
            if isinstance(value, str):
                assert "users/" not in value or value == progress.position

    def test_get_progress_response_has_no_file_ref(
        self, copy_repo, file_storage, progress_repo
    ):
        """GetReadingProgress response has no file_ref."""
        user_id = uuid4()
        copy = _make_digital_copy(user_id, file_storage, copy_repo)

        # Save progress first
        progress_repo.upsert(
            ReadingProgress(
                user_id=user_id,
                copy_id=copy.id,
                position="epubcfi(/6/4!/4/2/1:0)",
                file_format=FileFormat.EPUB,
                percentage=0.5,
            )
        )

        uc = GetReadingProgress(
            copy_repository=copy_repo,
            reading_progress_repository=progress_repo,
        )
        result = uc.execute(copy_id=copy.id, user_id=user_id)

        assert result is not None
        assert not hasattr(result, "file_ref")
        # No field reveals the underlying storage path
        for value in result.__dict__.values():
            if isinstance(value, str):
                assert "users/" not in value or value == result.position
