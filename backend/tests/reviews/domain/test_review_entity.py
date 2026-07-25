"""Domain unit tests for Review entity (Task 1).

Tests visibility invariants and rating validation.
Reference: reviews/design.md Properties 1-2
"""

from uuid import uuid4

import pytest

from app.reviews.domain.entities import Review, SharedWithType, Visibility


class TestReviewPrivateVisibility:
    """Property 1: private visibility → shared_with is None."""

    def test_valid_private_review(self):
        review = Review(
            user_id=uuid4(),
            book_id=uuid4(),
            rating=4,
            visibility=Visibility.PRIVATE,
        )
        assert review.visibility == Visibility.PRIVATE
        assert review.shared_with_type is None
        assert review.shared_with_id is None

    def test_private_review_with_optional_text(self):
        review = Review(
            user_id=uuid4(),
            book_id=uuid4(),
            rating=3,
            visibility=Visibility.PRIVATE,
            text="A great read!",
        )
        assert review.text == "A great read!"
        assert review.shared_with_type is None
        assert review.shared_with_id is None

    def test_private_with_shared_with_type_raises(self):
        with pytest.raises(ValueError, match="Private review"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=3,
                visibility=Visibility.PRIVATE,
                shared_with_type=SharedWithType.GROUP,
                shared_with_id=uuid4(),
            )

    def test_private_with_only_shared_with_id_raises(self):
        with pytest.raises(ValueError, match="Private review"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=3,
                visibility=Visibility.PRIVATE,
                shared_with_id=uuid4(),
            )

    def test_private_with_only_shared_with_type_raises(self):
        with pytest.raises(ValueError, match="Private review"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=3,
                visibility=Visibility.PRIVATE,
                shared_with_type=SharedWithType.CLUB,
            )


class TestReviewSharedVisibility:
    """Property 2: shared visibility → shared_with is non-None."""

    def test_valid_shared_review_with_group(self):
        group_id = uuid4()
        review = Review(
            user_id=uuid4(),
            book_id=uuid4(),
            rating=5,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        assert review.visibility == Visibility.SHARED
        assert review.shared_with_type == SharedWithType.GROUP
        assert review.shared_with_id == group_id

    def test_valid_shared_review_with_club(self):
        club_id = uuid4()
        review = Review(
            user_id=uuid4(),
            book_id=uuid4(),
            rating=2,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.CLUB,
            shared_with_id=club_id,
        )
        assert review.visibility == Visibility.SHARED
        assert review.shared_with_type == SharedWithType.CLUB
        assert review.shared_with_id == club_id

    def test_shared_without_shared_with_type_raises(self):
        with pytest.raises(ValueError, match="Shared review"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=4,
                visibility=Visibility.SHARED,
                shared_with_id=uuid4(),
            )

    def test_shared_without_shared_with_id_raises(self):
        with pytest.raises(ValueError, match="Shared review"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=4,
                visibility=Visibility.SHARED,
                shared_with_type=SharedWithType.GROUP,
            )

    def test_shared_without_any_shared_with_raises(self):
        with pytest.raises(ValueError, match="Shared review"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=4,
                visibility=Visibility.SHARED,
            )


class TestReviewRating:
    """Rating must be between 1 and 5 inclusive."""

    def test_rating_minimum_valid(self):
        review = Review(
            user_id=uuid4(),
            book_id=uuid4(),
            rating=1,
            visibility=Visibility.PRIVATE,
        )
        assert review.rating == 1

    def test_rating_maximum_valid(self):
        review = Review(
            user_id=uuid4(),
            book_id=uuid4(),
            rating=5,
            visibility=Visibility.PRIVATE,
        )
        assert review.rating == 5

    def test_rating_zero_raises(self):
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=0,
                visibility=Visibility.PRIVATE,
            )

    def test_rating_six_raises(self):
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=6,
                visibility=Visibility.PRIVATE,
            )

    def test_rating_negative_raises(self):
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            Review(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=-1,
                visibility=Visibility.PRIVATE,
            )
