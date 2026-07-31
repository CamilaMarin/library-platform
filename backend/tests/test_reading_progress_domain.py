"""Domain unit tests for ReadingProgress entity (Reader spec, Task 1).

Tests ownership invariant (Property 2) and format-appropriate positioning (Property 4).
Reference: .kiro/specs/reader/design.md, ADR-0014
"""

from uuid import uuid4

import pytest

from app.library.domain.entities import FileFormat, ReadingProgress


class TestReadingProgressCreation:
    """Basic creation and field defaults."""

    def test_valid_epub_progress(self):
        user_id = uuid4()
        progress = ReadingProgress(
            user_id=user_id,
            copy_id=uuid4(),
            position="epubcfi(/6/4!/4/2/1:0)",
            file_format=FileFormat.EPUB,
            percentage=0.45,
        )
        assert progress.user_id == user_id
        assert progress.position == "epubcfi(/6/4!/4/2/1:0)"
        assert progress.file_format == FileFormat.EPUB
        assert progress.percentage == 0.45
        assert progress.id is not None
        assert progress.last_read_at is not None

    def test_valid_pdf_progress(self):
        progress = ReadingProgress(
            user_id=uuid4(),
            copy_id=uuid4(),
            position="42",
            file_format=FileFormat.PDF,
            percentage=0.7,
        )
        assert progress.position == "42"
        assert progress.file_format == FileFormat.PDF

    def test_default_percentage_is_zero(self):
        progress = ReadingProgress(
            user_id=uuid4(),
            copy_id=uuid4(),
            position="1",
            file_format=FileFormat.PDF,
        )
        assert progress.percentage == 0.0


class TestPercentageValidation:
    """Percentage must be in [0.0, 1.0]."""

    def test_percentage_at_zero(self):
        progress = ReadingProgress(
            user_id=uuid4(),
            copy_id=uuid4(),
            position="1",
            file_format=FileFormat.PDF,
            percentage=0.0,
        )
        assert progress.percentage == 0.0

    def test_percentage_at_one(self):
        progress = ReadingProgress(
            user_id=uuid4(),
            copy_id=uuid4(),
            position="100",
            file_format=FileFormat.PDF,
            percentage=1.0,
        )
        assert progress.percentage == 1.0

    def test_percentage_below_zero_rejected(self):
        with pytest.raises(ValueError, match="Percentage must be between 0.0 and 1.0"):
            ReadingProgress(
                user_id=uuid4(),
                copy_id=uuid4(),
                position="1",
                file_format=FileFormat.PDF,
                percentage=-0.1,
            )

    def test_percentage_above_one_rejected(self):
        with pytest.raises(ValueError, match="Percentage must be between 0.0 and 1.0"):
            ReadingProgress(
                user_id=uuid4(),
                copy_id=uuid4(),
                position="1",
                file_format=FileFormat.PDF,
                percentage=1.01,
            )


class TestFormatAppropriatePositioning:
    """Property 4: EPUB uses CFI, PDF uses page numbers, never mixed."""

    def test_epub_requires_cfi_prefix(self):
        with pytest.raises(ValueError, match="EPUB position must be a CFI string"):
            ReadingProgress(
                user_id=uuid4(),
                copy_id=uuid4(),
                position="42",
                file_format=FileFormat.EPUB,
                percentage=0.5,
            )

    def test_epub_requires_cfi_closing_paren(self):
        with pytest.raises(ValueError, match="valid CFI string ending with"):
            ReadingProgress(
                user_id=uuid4(),
                copy_id=uuid4(),
                position="epubcfi(/6/4!/4/2/1:0",
                file_format=FileFormat.EPUB,
                percentage=0.5,
            )

    def test_epub_valid_cfi_accepted(self):
        progress = ReadingProgress(
            user_id=uuid4(),
            copy_id=uuid4(),
            position="epubcfi(/6/4!/4/2/1:0)",
            file_format=FileFormat.EPUB,
            percentage=0.25,
        )
        assert progress.position == "epubcfi(/6/4!/4/2/1:0)"

    def test_pdf_requires_positive_integer_string(self):
        with pytest.raises(ValueError, match="positive integer page number"):
            ReadingProgress(
                user_id=uuid4(),
                copy_id=uuid4(),
                position="epubcfi(/6/4!/4/2/1:0)",
                file_format=FileFormat.PDF,
                percentage=0.5,
            )

    def test_pdf_rejects_zero_page(self):
        with pytest.raises(ValueError, match="positive integer page number"):
            ReadingProgress(
                user_id=uuid4(),
                copy_id=uuid4(),
                position="0",
                file_format=FileFormat.PDF,
                percentage=0.0,
            )

    def test_pdf_rejects_negative_page(self):
        with pytest.raises(ValueError, match="positive integer page number"):
            ReadingProgress(
                user_id=uuid4(),
                copy_id=uuid4(),
                position="-1",
                file_format=FileFormat.PDF,
                percentage=0.0,
            )

    def test_pdf_rejects_non_numeric(self):
        with pytest.raises(ValueError, match="positive integer page number"):
            ReadingProgress(
                user_id=uuid4(),
                copy_id=uuid4(),
                position="page5",
                file_format=FileFormat.PDF,
                percentage=0.3,
            )

    def test_pdf_valid_page_number(self):
        progress = ReadingProgress(
            user_id=uuid4(),
            copy_id=uuid4(),
            position="150",
            file_format=FileFormat.PDF,
            percentage=0.6,
        )
        assert progress.position == "150"


class TestOwnershipInvariant:
    """Property 2: ReadingProgress can only exist where progress.user_id == copy.user_id."""

    def test_ownership_valid_when_same_user(self):
        user_id = uuid4()
        # Should not raise
        ReadingProgress.validate_ownership(user_id=user_id, copy_user_id=user_id)

    def test_ownership_rejected_when_different_user(self):
        with pytest.raises(ValueError, match="copies owned by the user"):
            ReadingProgress.validate_ownership(
                user_id=uuid4(), copy_user_id=uuid4()
            )
