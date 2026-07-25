"""Domain unit tests for Clubs (M5 Task 1).

Tests Club, ReadingTurn, Comment entities.
Reference: clubs/design.md Properties 1-3
"""

from uuid import uuid4

import pytest

from app.community.domain.entities import Club, Comment, ReadingTurn


class TestClub:
    def test_valid_club_creation(self):
        club = Club(group_id=uuid4(), name="Family Readers")
        assert club.name == "Family Readers"
        assert club.active_book_id is None
        assert club.discussion_date is None

    def test_club_requires_name(self):
        with pytest.raises(ValueError, match="name"):
            Club(group_id=uuid4(), name="")

    def test_club_group_id_is_singular(self):
        """Property 2: group_id is a single UUID, not an array."""
        group_id = uuid4()
        club = Club(group_id=group_id, name="Test Club")
        assert club.group_id == group_id
        assert isinstance(club.group_id, type(uuid4()))


class TestReadingTurn:
    def test_valid_reading_turn(self):
        turn = ReadingTurn(
            club_id=uuid4(),
            book_id=uuid4(),
            current_user_id=uuid4(),
        )
        assert turn.club_id is not None
        assert turn.book_id is not None
        assert turn.current_user_id is not None


class TestComment:
    def test_valid_comment(self):
        comment = Comment(
            turn_id=uuid4(),
            user_id=uuid4(),
            text="Great chapter!",
        )
        assert comment.text == "Great chapter!"
        assert comment.is_spoiler is False

    def test_spoiler_defaults_to_false(self):
        """Property 3: is_spoiler defaults to False."""
        comment = Comment(
            turn_id=uuid4(),
            user_id=uuid4(),
            text="This is fine",
        )
        assert comment.is_spoiler is False

    def test_spoiler_can_be_explicitly_set(self):
        comment = Comment(
            turn_id=uuid4(),
            user_id=uuid4(),
            text="He dies at the end!",
            is_spoiler=True,
        )
        assert comment.is_spoiler is True

    def test_comment_requires_text(self):
        with pytest.raises(ValueError, match="text"):
            Comment(turn_id=uuid4(), user_id=uuid4(), text="")
