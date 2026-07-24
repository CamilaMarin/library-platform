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
