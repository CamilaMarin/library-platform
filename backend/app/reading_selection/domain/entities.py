"""Reading Selection domain entities.

Pure domain objects — no framework or infrastructure imports.
Reference: ADR-0008 (availability rule), ADR-0013 (dedicated spec)
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.library.domain.entities import Copy, CopyStatus, CopyType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Draw:
    """A reading draw result for a family group.

    Records the selected book and which user's library it came from.
    """

    id: UUID = field(default_factory=uuid4)
    group_id: UUID = field(default_factory=uuid4)
    filters: dict = field(default_factory=dict)
    participants: list[UUID] = field(default_factory=list)
    result_book_id: UUID | None = None
    result_source_user_id: UUID | None = None
    timestamp: datetime = field(default_factory=_utcnow)


@dataclass
class TurnHistory:
    """Tracks who last picked in pick-by-turn mode.

    The member with the oldest (or null) last_pick_date picks next.
    """

    id: UUID = field(default_factory=uuid4)
    group_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    last_pick_date: datetime | None = None


def check_availability(copies: list[Copy], participant_ids: list[UUID]) -> bool:
    """Check if every participant has authorized access to a book.

    Physical books: participant owns a copy with status == available.
    Digital books: participant owns a copy (ownership is sufficient).

    Reference: ADR-0008 (availability rule), Property 1 & 2
    """
    for participant_id in participant_ids:
        participant_copies = [c for c in copies if c.user_id == participant_id]
        if not participant_copies:
            return False

        # At least one copy must be accessible
        has_access = False
        for copy in participant_copies:
            if copy.type == CopyType.DIGITAL:
                # Digital: ownership is sufficient
                has_access = True
                break
            elif copy.type == CopyType.PHYSICAL and copy.status == CopyStatus.AVAILABLE:
                # Physical: must be available (not on loan)
                has_access = True
                break

        if not has_access:
            return False

    return True


def select_random_book(
    candidate_book_ids: list[UUID],
) -> UUID | None:
    """Select a random book from candidates. Returns None if no candidates."""
    if not candidate_book_ids:
        return None
    return random.choice(candidate_book_ids)


def determine_next_picker(turn_histories: list[TurnHistory]) -> UUID | None:
    """Determine who picks next in pick-by-turn mode.

    The member with the oldest (or null) last_pick_date goes next.
    Property 5: deterministic rotation.
    """
    if not turn_histories:
        return None

    # Members who never picked go first (null last_pick_date)
    never_picked = [th for th in turn_histories if th.last_pick_date is None]
    if never_picked:
        return never_picked[0].user_id

    # Otherwise, oldest last_pick_date
    sorted_histories = sorted(turn_histories, key=lambda th: th.last_pick_date)
    return sorted_histories[0].user_id
