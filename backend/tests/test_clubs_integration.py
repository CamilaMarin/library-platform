"""Integration tests for Clubs (M5 Task 6).

Tests use cases with in-memory test doubles.
Validates Properties 1-3.

Reference: clubs/design.md, ADR-0001, ADR-0006, ADR-0009
"""

from uuid import uuid4

import pytest

from app.community.application.activate_reading_turn import (
    ActivateReadingTurn,
    CopyOwnershipError,
)
from app.community.application.create_club import CreateClub
from app.community.application.post_comment import PostComment
from app.community.application.set_active_book import SetActiveBook
from app.community.domain.entities import Club, Comment, ReadingTurn

# --- In-memory test doubles ---


class InMemoryClubRepository:
    def __init__(self):
        self.clubs: dict = {}

    def save(self, club: Club) -> Club:
        self.clubs[club.id] = club
        return club

    def find_by_id(self, club_id):
        return self.clubs.get(club_id)

    def update(self, club: Club) -> Club:
        self.clubs[club.id] = club
        return club


class InMemoryReadingTurnRepository:
    def __init__(self):
        self.turns: list[ReadingTurn] = []

    def save(self, turn: ReadingTurn) -> ReadingTurn:
        self.turns.append(turn)
        return turn

    def find_by_club(self, club_id):
        return [t for t in self.turns if t.club_id == club_id]


class InMemoryCommentRepository:
    def __init__(self):
        self.comments: list[Comment] = []

    def save(self, comment: Comment) -> Comment:
        self.comments.append(comment)
        return comment

    def find_by_turn(self, turn_id):
        return [c for c in self.comments if c.turn_id == turn_id]


class InMemoryCopyOwnershipQuery:
    """Test double for ownership check."""

    def __init__(self, owned_pairs: set[tuple] | None = None):
        self._owned = owned_pairs or set()

    def user_owns_copy_of_book(self, user_id, book_id) -> bool:
        return (user_id, book_id) in self._owned


# --- Tests ---


class TestCreateClub:
    def test_creates_club_successfully(self):
        repo = InMemoryClubRepository()
        uc = CreateClub(club_repository=repo)
        club = uc.execute(group_id=uuid4(), name="Book Lovers")
        assert club.name == "Book Lovers"
        assert repo.find_by_id(club.id) is not None

    def test_club_belongs_to_single_group(self):
        """Property 2: group_id is singular."""
        repo = InMemoryClubRepository()
        uc = CreateClub(club_repository=repo)
        group_id = uuid4()
        club = uc.execute(group_id=group_id, name="Family Club")
        assert club.group_id == group_id


class TestSetActiveBook:
    def test_sets_active_book(self):
        repo = InMemoryClubRepository()
        club = Club(group_id=uuid4(), name="Test Club")
        repo.save(club)

        uc = SetActiveBook(club_repository=repo)
        book_id = uuid4()
        uc.execute(club_id=club.id, book_id=book_id)

        updated = repo.find_by_id(club.id)
        assert updated.active_book_id == book_id

    def test_club_not_found_raises(self):
        repo = InMemoryClubRepository()
        uc = SetActiveBook(club_repository=repo)
        with pytest.raises(ValueError, match="not found"):
            uc.execute(club_id=uuid4(), book_id=uuid4())


class TestPostComment:
    def test_posts_comment_with_default_spoiler_false(self):
        """Property 3: is_spoiler defaults to False."""
        repo = InMemoryCommentRepository()
        uc = PostComment(comment_repository=repo)
        comment = uc.execute(turn_id=uuid4(), user_id=uuid4(), text="Great!")
        assert comment.text == "Great!"
        assert comment.is_spoiler is False

    def test_posts_comment_with_spoiler_true(self):
        repo = InMemoryCommentRepository()
        uc = PostComment(comment_repository=repo)
        comment = uc.execute(
            turn_id=uuid4(), user_id=uuid4(), text="He dies!", is_spoiler=True
        )
        assert comment.is_spoiler is True


class TestActivateReadingTurn:
    def test_activates_when_user_owns_copy(self):
        """Property 1: succeeds when user owns a copy."""
        club_repo = InMemoryClubRepository()
        turn_repo = InMemoryReadingTurnRepository()
        user_id = uuid4()
        book_id = uuid4()

        club = Club(group_id=uuid4(), name="Readers")
        club.active_book_id = book_id
        club_repo.save(club)

        ownership = InMemoryCopyOwnershipQuery(owned_pairs={(user_id, book_id)})

        uc = ActivateReadingTurn(
            club_repository=club_repo,
            turn_repository=turn_repo,
            copy_ownership=ownership,
        )
        turn = uc.execute(club_id=club.id, user_id=user_id)
        assert turn.current_user_id == user_id
        assert turn.book_id == book_id

    def test_rejects_when_user_does_not_own_copy(self):
        """Property 1: fails when user doesn't own a copy (409)."""
        club_repo = InMemoryClubRepository()
        turn_repo = InMemoryReadingTurnRepository()
        user_id = uuid4()
        book_id = uuid4()

        club = Club(group_id=uuid4(), name="Readers")
        club.active_book_id = book_id
        club_repo.save(club)

        ownership = InMemoryCopyOwnershipQuery(owned_pairs=set())

        uc = ActivateReadingTurn(
            club_repository=club_repo,
            turn_repository=turn_repo,
            copy_ownership=ownership,
        )
        with pytest.raises(CopyOwnershipError):
            uc.execute(club_id=club.id, user_id=user_id)

    def test_rejects_when_no_active_book(self):
        club_repo = InMemoryClubRepository()
        turn_repo = InMemoryReadingTurnRepository()
        ownership = InMemoryCopyOwnershipQuery()

        club = Club(group_id=uuid4(), name="Empty Club")
        club_repo.save(club)

        uc = ActivateReadingTurn(
            club_repository=club_repo,
            turn_repository=turn_repo,
            copy_ownership=ownership,
        )
        with pytest.raises(ValueError, match="no active book"):
            uc.execute(club_id=club.id, user_id=uuid4())
