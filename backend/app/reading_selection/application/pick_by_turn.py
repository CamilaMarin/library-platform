"""PickByTurn use case.

Fair rotation: the member with the oldest (or null) last_pick_date picks next.

Reference: reading-selection/requirements.md Req 2, Property 5
"""

from datetime import datetime, timezone
from uuid import UUID

from app.reading_selection.application.protocols import TurnHistoryRepository
from app.reading_selection.domain.entities import TurnHistory, determine_next_picker


class PickByTurn:
    """Use case: determine who picks next and record their pick.

    Rotation is deterministic: next picker is the member with the oldest
    (or null) last_pick_date.
    """

    def __init__(self, turn_history_repository: TurnHistoryRepository):
        self._turn_repo = turn_history_repository

    def get_next_picker(self, group_id: UUID) -> UUID | None:
        """Determine who picks next without recording a pick."""
        histories = self._turn_repo.find_by_group(group_id)
        return determine_next_picker(histories)

    def record_pick(self, group_id: UUID, user_id: UUID) -> TurnHistory:
        """Record that a user has made their pick. Updates their last_pick_date."""
        histories = self._turn_repo.find_by_group(group_id)

        # Find or create the user's turn history
        existing = next((h for h in histories if h.user_id == user_id), None)

        if existing:
            existing.last_pick_date = datetime.now(timezone.utc)
            return self._turn_repo.save_or_update(existing)
        else:
            new_turn = TurnHistory(
                group_id=group_id,
                user_id=user_id,
                last_pick_date=datetime.now(timezone.utc),
            )
            return self._turn_repo.save_or_update(new_turn)
