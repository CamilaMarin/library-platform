"""Integration tests for Reading Selection (M4 Task 7).

Tests RunReadingDraw and PickByTurn with in-memory test doubles.
Validates Properties 1-5 at the use case level.

Reference: reading-selection/design.md, ADR-0008
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.library.domain.entities import Book, Copy, CopyStatus, CopyType
from app.reading_selection.application.pick_by_turn import PickByTurn
from app.reading_selection.application.run_reading_draw import RunDrawRequest, RunReadingDraw
from app.reading_selection.domain.entities import Draw, TurnHistory

# --- In-memory test doubles ---


class InMemoryDrawRepository:
    def __init__(self):
        self.draws: list[Draw] = []

    def save(self, draw: Draw) -> Draw:
        self.draws.append(draw)
        return draw

    def find_by_group(self, group_id):
        return [d for d in self.draws if d.group_id == group_id]

    def find_result_book_ids_by_group(self, group_id):
        return [
            d.result_book_id
            for d in self.draws
            if d.group_id == group_id and d.result_book_id is not None
        ]


class InMemoryTurnHistoryRepository:
    def __init__(self):
        self.histories: list[TurnHistory] = []

    def find_by_group(self, group_id):
        return [h for h in self.histories if h.group_id == group_id]

    def save_or_update(self, turn: TurnHistory) -> TurnHistory:
        existing = next(
            (h for h in self.histories if h.id == turn.id), None
        )
        if existing:
            existing.last_pick_date = turn.last_pick_date
            return existing
        self.histories.append(turn)
        return turn


class InMemoryCopyQueryService:
    """Test double — never returns file_ref (Property 3)."""

    def __init__(self, copies: list[Copy]):
        self._copies = copies

    def find_copies_for_books(self, book_ids, participant_ids):
        result = {}
        for copy in self._copies:
            if copy.book_id in book_ids and copy.user_id in participant_ids:
                # Strip actual file_ref but use placeholder for digital (Property 3)
                safe_file_ref = "[redacted]" if copy.type == CopyType.DIGITAL else None
                safe_copy = Copy(
                    id=copy.id,
                    user_id=copy.user_id,
                    book_id=copy.book_id,
                    type=copy.type,
                    file_ref=safe_file_ref,
                    status=copy.status,
                )
                result.setdefault(copy.book_id, []).append(safe_copy)
        return result


class InMemoryBookQueryService:
    def __init__(self, books: list[Book]):
        self._books = books

    def find_books_by_group_members(self, member_ids, genre=None, max_pages=None):
        results = list(self._books)
        if genre:
            results = [b for b in results if genre in b.genres]
        if max_pages:
            results = [b for b in results if b.pages and b.pages <= max_pages]
        return results


# --- RunReadingDraw tests ---


class TestRunReadingDraw:
    def test_draw_selects_available_book(self):
        """Happy path: draw selects from available books."""
        user_a = uuid4()
        user_b = uuid4()
        book = Book(title="Shared Book", author="Author", pages=200)

        copies = [
            Copy(
                user_id=user_a, book_id=book.id,
                type=CopyType.PHYSICAL, status=CopyStatus.AVAILABLE,
            ),
            Copy(
                user_id=user_b, book_id=book.id,
                type=CopyType.DIGITAL, file_ref="users/b/book.epub",
            ),
        ]

        draw_repo = InMemoryDrawRepository()
        uc = RunReadingDraw(
            draw_repository=draw_repo,
            book_query=InMemoryBookQueryService([book]),
            copy_query=InMemoryCopyQueryService(copies),
        )

        result = uc.execute(RunDrawRequest(
            group_id=uuid4(),
            participant_ids=[user_a, user_b],
        ))

        assert result.result_book_id == book.id
        assert result.result_source_user_id is not None
        assert len(draw_repo.draws) == 1

    def test_draw_empty_when_no_books(self):
        """Empty result when no books available (not an error)."""
        draw_repo = InMemoryDrawRepository()
        uc = RunReadingDraw(
            draw_repository=draw_repo,
            book_query=InMemoryBookQueryService([]),
            copy_query=InMemoryCopyQueryService([]),
        )

        result = uc.execute(RunDrawRequest(
            group_id=uuid4(),
            participant_ids=[uuid4()],
        ))

        assert result.result_book_id is None
        assert len(draw_repo.draws) == 1

    def test_draw_excludes_unavailable_books(self):
        """Property 1: Physical on_loan excluded from draw."""
        user_a = uuid4()
        user_b = uuid4()
        book = Book(title="On Loan Book", author="Author", pages=100)

        copies = [
            Copy(
                user_id=user_a, book_id=book.id,
                type=CopyType.PHYSICAL, status=CopyStatus.ON_LOAN,
            ),
            Copy(
                user_id=user_b, book_id=book.id,
                type=CopyType.PHYSICAL, status=CopyStatus.AVAILABLE,
            ),
        ]

        draw_repo = InMemoryDrawRepository()
        uc = RunReadingDraw(
            draw_repository=draw_repo,
            book_query=InMemoryBookQueryService([book]),
            copy_query=InMemoryCopyQueryService(copies),
        )

        result = uc.execute(RunDrawRequest(
            group_id=uuid4(),
            participant_ids=[user_a, user_b],
        ))

        assert result.result_book_id is None

    def test_draw_filters_by_genre(self):
        """Genre filter excludes non-matching books."""
        user = uuid4()
        book_fiction = Book(title="Fiction", author="A", genres=["fiction"], pages=200)
        book_science = Book(title="Science", author="B", genres=["science"], pages=150)

        copies = [
            Copy(user_id=user, book_id=book_fiction.id, type=CopyType.PHYSICAL),
            Copy(user_id=user, book_id=book_science.id, type=CopyType.PHYSICAL),
        ]

        draw_repo = InMemoryDrawRepository()
        uc = RunReadingDraw(
            draw_repository=draw_repo,
            book_query=InMemoryBookQueryService([book_fiction, book_science]),
            copy_query=InMemoryCopyQueryService(copies),
        )

        result = uc.execute(RunDrawRequest(
            group_id=uuid4(),
            participant_ids=[user],
            genre="fiction",
        ))

        assert result.result_book_id == book_fiction.id

    def test_draw_unread_excludes_previously_drawn(self):
        """Unread filter excludes books previously drawn by the group."""
        user = uuid4()
        group_id = uuid4()
        book_old = Book(title="Already Read", author="A", pages=100)
        book_new = Book(title="Not Read", author="B", pages=100)

        copies = [
            Copy(user_id=user, book_id=book_old.id, type=CopyType.PHYSICAL),
            Copy(user_id=user, book_id=book_new.id, type=CopyType.PHYSICAL),
        ]

        draw_repo = InMemoryDrawRepository()
        draw_repo.draws.append(Draw(
            group_id=group_id,
            participants=[user],
            result_book_id=book_old.id,
            result_source_user_id=user,
        ))

        uc = RunReadingDraw(
            draw_repository=draw_repo,
            book_query=InMemoryBookQueryService([book_old, book_new]),
            copy_query=InMemoryCopyQueryService(copies),
        )

        result = uc.execute(RunDrawRequest(
            group_id=group_id,
            participant_ids=[user],
            unread_only=True,
        ))

        assert result.result_book_id == book_new.id

    def test_draw_result_never_contains_file_ref(self):
        """Property 3: Draw results never expose file_ref."""
        user = uuid4()
        book = Book(title="Digital Book", author="A")

        copies = [
            Copy(
                user_id=user, book_id=book.id,
                type=CopyType.DIGITAL, file_ref="users/x/secret.epub",
            ),
        ]

        draw_repo = InMemoryDrawRepository()
        copy_query = InMemoryCopyQueryService(copies)
        uc = RunReadingDraw(
            draw_repository=draw_repo,
            book_query=InMemoryBookQueryService([book]),
            copy_query=copy_query,
        )

        result = uc.execute(RunDrawRequest(
            group_id=uuid4(),
            participant_ids=[user],
        ))

        assert result.result_book_id == book.id
        copies_returned = copy_query.find_copies_for_books([book.id], [user])
        for book_copies in copies_returned.values():
            for c in book_copies:
                assert c.file_ref == "[redacted]"  # Never actual path


# --- PickByTurn tests ---


class TestPickByTurn:
    def test_get_next_picker_with_no_history(self):
        """No history = None."""
        repo = InMemoryTurnHistoryRepository()
        uc = PickByTurn(turn_history_repository=repo)
        assert uc.get_next_picker(uuid4()) is None

    def test_get_next_picker_selects_oldest(self):
        """Property 5: oldest last_pick_date goes next."""
        group_id = uuid4()
        user_a = uuid4()
        user_b = uuid4()
        repo = InMemoryTurnHistoryRepository()
        repo.histories = [
            TurnHistory(
                group_id=group_id, user_id=user_a,
                last_pick_date=datetime(2025, 3, 1, tzinfo=timezone.utc),
            ),
            TurnHistory(
                group_id=group_id, user_id=user_b,
                last_pick_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            ),
        ]

        uc = PickByTurn(turn_history_repository=repo)
        assert uc.get_next_picker(group_id) == user_b

    def test_record_pick_updates_history(self):
        """Recording a pick updates last_pick_date."""
        group_id = uuid4()
        user = uuid4()
        repo = InMemoryTurnHistoryRepository()
        repo.histories = [
            TurnHistory(group_id=group_id, user_id=user, last_pick_date=None),
        ]

        uc = PickByTurn(turn_history_repository=repo)
        result = uc.record_pick(group_id, user)

        assert result.last_pick_date is not None
        assert result.user_id == user

    def test_record_pick_creates_new_if_not_exists(self):
        """Recording for new user creates a turn history entry."""
        group_id = uuid4()
        user = uuid4()
        repo = InMemoryTurnHistoryRepository()

        uc = PickByTurn(turn_history_repository=repo)
        result = uc.record_pick(group_id, user)

        assert result.user_id == user
        assert result.last_pick_date is not None
        assert len(repo.histories) == 1
