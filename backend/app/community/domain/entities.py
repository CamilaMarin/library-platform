"""Community domain entities.

Pure domain objects — no framework or infrastructure imports.
Reference: ADR-0006 (single group only), clubs/design.md
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Club:
    """Aggregate root: book club within a single family group.

    group_id is singular (not array) — multi-group clubs removed from MVP (ADR-0006).
    """

    id: UUID = field(default_factory=uuid4)
    group_id: UUID = field(default_factory=uuid4)
    name: str = ""
    active_book_id: UUID | None = None
    discussion_date: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        if not self.name:
            raise ValueError("Club requires a name")


@dataclass
class ReadingTurn:
    """Entity within Club: coordinates who reads/comments on a digital book.

    Activation requires the user to own their own copy (Property 1).
    Never transfers the file between accounts (ADR-0001).
    """

    id: UUID = field(default_factory=uuid4)
    club_id: UUID = field(default_factory=uuid4)
    book_id: UUID = field(default_factory=uuid4)
    current_user_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utcnow)


@dataclass
class Comment:
    """Comment on a reading turn.

    is_spoiler defaults to False — users must explicitly mark spoilers (Property 3).
    """

    id: UUID = field(default_factory=uuid4)
    turn_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    text: str = ""
    is_spoiler: bool = False
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        if not self.text:
            raise ValueError("Comment requires text")
