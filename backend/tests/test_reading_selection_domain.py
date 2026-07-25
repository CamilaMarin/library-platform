"""Domain unit tests for Reading Selection (M4 Tasks 1, 5).

Tests availability validation and turn rotation logic.
Reference: reading-selection/design.md Properties 1-2, 5
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.library.domain.entities import Copy, CopyStatus, CopyType
from app.reading_selection.domain.entities import (
    TurnHistory,
    check_availability,
    determine_next_picker,
    select_random_book,
)


def _make_datetime(year, month, day):
    return datetime(year, month, day, tzinfo=timezone.utc)


class TestAvailability:
    def test_physical_available_passes(self):
        """Property 1: Physical with status available = accessible."""
        user = uuid4()
        book_id = uuid4()
        copies = [
            Copy(
                user_id=user, book_id=book_id, type=CopyType.PHYSICAL,
                status=CopyStatus.AVAILABLE,
            )
        ]
        assert check_availability(copies, [user]) is True

    def test_physical_on_loan_fails(self):
        """Property 1: Physical on_loan = not accessible."""
        user = uuid4()
        book_id = uuid4()
        copies = [
            Copy(
                user_id=user, book_id=book_id, type=CopyType.PHYSICAL,
                status=CopyStatus.ON_LOAN,
            )
        ]
        assert check_availability(copies, [user]) is False

    def test_digital_always_accessible(self):
        """Property 2: Digital ownership is sufficient."""
        user = uuid4()
        book_id = uuid4()
        copies = [
            Copy(
                user_id=user, book_id=book_id, type=CopyType.DIGITAL,
                file_ref="users/x/book.epub",
            )
        ]
        assert check_availability(copies, [user]) is True

    def test_participant_without_copy_fails(self):
        """All participants must have access."""
        user_a = uuid4()
        user_b = uuid4()
        book_id = uuid4()
        copies = [
            Copy(
                user_id=user_a, book_id=book_id, type=CopyType.PHYSICAL,
                status=CopyStatus.AVAILABLE,
            )
        ]
        assert check_availability(copies, [user_a, user_b]) is False

    def test_all_participants_with_copies_passes(self):
        user_a = uuid4()
        user_b = uuid4()
        book_id = uuid4()
        copies = [
            Copy(
                user_id=user_a, book_id=book_id, type=CopyType.PHYSICAL,
                status=CopyStatus.AVAILABLE,
            ),
            Copy(
                user_id=user_b, book_id=book_id, type=CopyType.DIGITAL,
                file_ref="users/b/book.pdf",
            ),
        ]
        assert check_availability(copies, [user_a, user_b]) is True

    def test_empty_participants_passes(self):
        """Edge: no participants = trivially satisfied."""
        assert check_availability([], []) is True


class TestSelectRandomBook:
    def test_returns_from_candidates(self):
        book_ids = [uuid4(), uuid4(), uuid4()]
        result = select_random_book(book_ids)
        assert result in book_ids

    def test_empty_candidates_returns_none(self):
        assert select_random_book([]) is None


class TestDetermineNextPicker:
    def test_never_picked_goes_first(self):
        """Members who never picked go first."""
        group = uuid4()
        user_a = uuid4()
        user_b = uuid4()
        histories = [
            TurnHistory(group_id=group, user_id=user_a, last_pick_date=None),
            TurnHistory(
                group_id=group, user_id=user_b,
                last_pick_date=_make_datetime(2025, 1, 1),
            ),
        ]
        assert determine_next_picker(histories) == user_a

    def test_oldest_pick_goes_next(self):
        """Property 5: oldest last_pick_date goes next."""
        group = uuid4()
        user_a = uuid4()
        user_b = uuid4()
        histories = [
            TurnHistory(
                group_id=group, user_id=user_a,
                last_pick_date=_make_datetime(2025, 3, 1),
            ),
            TurnHistory(
                group_id=group, user_id=user_b,
                last_pick_date=_make_datetime(2025, 1, 1),
            ),
        ]
        assert determine_next_picker(histories) == user_b

    def test_empty_histories_returns_none(self):
        assert determine_next_picker([]) is None
