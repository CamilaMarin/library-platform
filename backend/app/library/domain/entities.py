"""Library domain entities.

Pure domain objects — no framework or infrastructure imports.
Reference: ADR-0001 (no file sharing), ADR-0015 (Book/Copy separation)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CopyType(str, Enum):
    """Type of book copy."""

    PHYSICAL = "physical"
    DIGITAL = "digital"


class CopyStatus(str, Enum):
    """Availability status of a copy."""

    AVAILABLE = "available"
    ON_LOAN = "on_loan"


class ReadingStatusValue(str, Enum):
    """Personal reading status a user assigns to a book.

    Belongs to the (user, book) pair — independent of copy count.
    Reference: .kiro/specs/reading-status/design.md
    """

    WANT_TO_READ = "want_to_read"
    READING = "reading"
    READ = "read"
    DNF = "dnf"


@dataclass
class Book:
    """Catalog entity representing an intellectual work.

    Can exist without any copies (ADR-0015 Property 1).
    Contains shareable metadata — never file references.
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    author: str = ""
    genres: list[str] = field(default_factory=list)
    description: str = ""
    pages: int | None = None
    isbn: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        if not self.title:
            raise ValueError("Book requires a title")
        if not self.author:
            raise ValueError("Book requires an author")


@dataclass
class Copy:
    """Aggregate root representing an owned instance of a Book.

    Each copy has exactly one owner (user_id), immutable after creation.
    Physical: metadata + status only. Digital: file_ref (never exposed outside owner).

    Invariants:
    - type == PHYSICAL implies file_ref is None (Property 3)
    - file_ref is only resolved when request.user_id == user_id (Property 2)
    - A Copy cannot have two simultaneous active loans (enforced by Loans module)
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    book_id: UUID = field(default_factory=uuid4)
    type: CopyType = CopyType.PHYSICAL
    file_ref: str | None = None
    status: CopyStatus = CopyStatus.AVAILABLE
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        if self.type == CopyType.PHYSICAL and self.file_ref is not None:
            raise ValueError("Physical copy cannot have a file_ref")
        if self.type == CopyType.DIGITAL and not self.file_ref:
            raise ValueError("Digital copy requires a file_ref")


@dataclass
class ReadingStatus:
    """Personal reading status for a (user, book) pair.

    Key invariant: at most one record per (user_id, book_id) — enforced at DB level
    via UNIQUE constraint. See Property 1 in spec.

    This entity belongs to the Library bounded context.
    Privacy: included in ARCO export; deleted via ON DELETE CASCADE on user_id.
    """

    user_id: UUID
    book_id: UUID
    status: ReadingStatusValue
    current_page: int | None = None
    id: UUID = field(default_factory=uuid4)
    updated_at: datetime = field(default_factory=_utcnow)


class FileFormat(str, Enum):
    """Supported digital file formats for the integrated reader."""

    EPUB = "epub"
    PDF = "pdf"


@dataclass
class ReadingProgress:
    """Tracks a user's reading position in a digital copy.

    Personal data under Ley 21.719 (Chile's Data Protection Law) —
    included in ARCO export; deleted via ON DELETE CASCADE on user_id.

    Reference: .kiro/specs/reader/design.md, ADR-0014

    Invariants:
    - Ownership: progress.user_id must match the copy's user_id (Property 2).
    - Format-appropriate positioning: EPUB uses CFI strings, PDF uses page numbers (Property 4).
    - Percentage range: 0.0 <= percentage <= 1.0.
    """

    user_id: UUID
    copy_id: UUID
    position: str
    file_format: FileFormat
    percentage: float = 0.0
    id: UUID = field(default_factory=uuid4)
    last_read_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        self._validate_percentage()
        self._validate_position_format()

    def _validate_percentage(self) -> None:
        if not (0.0 <= self.percentage <= 1.0):
            raise ValueError(
                f"Percentage must be between 0.0 and 1.0, got {self.percentage}"
            )

    def _validate_position_format(self) -> None:
        """Enforce format-appropriate positioning (Property 4).

        EPUB: must be a CFI string starting with 'epubcfi('.
        PDF: must be a string representing a positive integer (page number).
        """
        if self.file_format == FileFormat.EPUB:
            if not self.position.startswith("epubcfi("):
                raise ValueError(
                    "EPUB position must be a CFI string starting with 'epubcfi('"
                )
            if not self.position.endswith(")"):
                raise ValueError(
                    "EPUB position must be a valid CFI string ending with ')'"
                )
        elif self.file_format == FileFormat.PDF:
            if not self.position.isdigit() or int(self.position) < 1:
                raise ValueError(
                    "PDF position must be a string representing a positive integer page number"
                )

    @staticmethod
    def validate_ownership(user_id: UUID, copy_user_id: UUID) -> None:
        """Validate ownership invariant (Property 2).

        ReadingProgress can only exist where progress.user_id == copy.user_id.
        Raises ValueError if ownership check fails.
        """
        if user_id != copy_user_id:
            raise ValueError(
                "ReadingProgress can only be created for copies owned by the user"
            )
