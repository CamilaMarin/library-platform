"""Reviews domain entities.

Pure domain objects — no framework or infrastructure imports.
Reference: ADR-0007 (review visibility model)

Invariants:
- visibility == 'private' implies shared_with_type IS NULL AND shared_with_id IS NULL
- visibility == 'shared' implies shared_with_type IS NOT NULL AND shared_with_id IS NOT NULL
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Visibility(str, Enum):
    """Review visibility choice — always explicit, never defaults to shared."""

    PRIVATE = "private"
    SHARED = "shared"


class SharedWithType(str, Enum):
    """Target type when visibility is shared."""

    GROUP = "group"
    CLUB = "club"


@dataclass
class Review:
    """Aggregate root: book review with explicit visibility control.

    Every review is either private (author only) or shared with exactly one
    specific group or club. No review is ever publicly visible.

    Invariants (ADR-0007, Properties 1-2):
    - Private: shared_with_type and shared_with_id MUST be None.
    - Shared: shared_with_type and shared_with_id MUST be non-None.
    """

    user_id: UUID = field(default_factory=uuid4)
    book_id: UUID = field(default_factory=uuid4)
    rating: int = 1
    visibility: Visibility = Visibility.PRIVATE
    text: str | None = None
    shared_with_type: SharedWithType | None = None
    shared_with_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        # Rating validation: integer 1-5
        if not (1 <= self.rating <= 5):
            raise ValueError("Rating must be between 1 and 5")

        # Visibility invariants (ADR-0007)
        if self.visibility == Visibility.PRIVATE:
            if self.shared_with_type is not None or self.shared_with_id is not None:
                raise ValueError(
                    "Private review must not have shared_with_type or shared_with_id"
                )
        elif self.visibility == Visibility.SHARED:
            if self.shared_with_type is None or self.shared_with_id is None:
                raise ValueError(
                    "Shared review requires both shared_with_type and shared_with_id"
                )
