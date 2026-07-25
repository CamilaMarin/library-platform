"""Tests for Reviews privacy integration: ARCO export and account cancellation.

Covers:
- ExportReviews use case (returns all user's reviews — private and shared)
- DeleteUserReviews use case (deletes all user's reviews)
- After deletion, reviews are no longer found in the database

Reference: reviews/requirements.md Req 2.3, ADR-0003
"""

from uuid import uuid4

import pytest

from app.reviews.application.delete_user_reviews import DeleteUserReviews
from app.reviews.application.export_reviews import ExportReviews
from app.reviews.domain.entities import Review, SharedWithType, Visibility
from app.reviews.infrastructure.repositories import SqlReviewRepository
from tests.conftest import TestSession


class TestExportReviews:
    """Unit tests for ExportReviews use case."""

    def _get_session(self):
        return TestSession()

    def test_export_returns_all_user_reviews(self):
        """Export returns both private and shared reviews for the user."""
        db = self._get_session()
        try:
            repo = SqlReviewRepository(db)
            user_id = uuid4()
            book_id = uuid4()
            group_id = uuid4()

            # Create a private review
            private_review = Review(
                user_id=user_id,
                book_id=book_id,
                rating=4,
                text="My private thoughts",
                visibility=Visibility.PRIVATE,
            )
            repo.save(private_review)

            # Create a shared review
            shared_review = Review(
                user_id=user_id,
                book_id=uuid4(),
                rating=5,
                text="Great book for the club",
                visibility=Visibility.SHARED,
                shared_with_type=SharedWithType.GROUP,
                shared_with_id=group_id,
            )
            repo.save(shared_review)
            db.commit()

            # Execute export
            use_case = ExportReviews(review_repository=repo)
            result = use_case.execute(user_id)

            # Verify all reviews are exported
            assert len(result.reviews) == 2

            # Verify private review data
            exported_private = next(
                r for r in result.reviews if r.id == private_review.id
            )
            assert exported_private.book_id == book_id
            assert exported_private.rating == 4
            assert exported_private.text == "My private thoughts"
            assert exported_private.visibility == "private"
            assert exported_private.shared_with_type is None
            assert exported_private.shared_with_id is None

            # Verify shared review data
            exported_shared = next(
                r for r in result.reviews if r.id == shared_review.id
            )
            assert exported_shared.rating == 5
            assert exported_shared.text == "Great book for the club"
            assert exported_shared.visibility == "shared"
            assert exported_shared.shared_with_type == "group"
            assert exported_shared.shared_with_id == group_id
        finally:
            db.close()

    def test_export_returns_empty_for_user_with_no_reviews(self):
        """Export returns empty list when user has no reviews."""
        db = self._get_session()
        try:
            repo = SqlReviewRepository(db)
            use_case = ExportReviews(review_repository=repo)

            result = use_case.execute(uuid4())

            assert result.reviews == []
        finally:
            db.close()

    def test_export_does_not_include_other_users_reviews(self):
        """Export only returns reviews belonging to the specified user."""
        db = self._get_session()
        try:
            repo = SqlReviewRepository(db)
            user_a = uuid4()
            user_b = uuid4()
            book_id = uuid4()

            # User A's review
            review_a = Review(
                user_id=user_a,
                book_id=book_id,
                rating=3,
                text="User A's review",
                visibility=Visibility.PRIVATE,
            )
            repo.save(review_a)

            # User B's review
            review_b = Review(
                user_id=user_b,
                book_id=book_id,
                rating=5,
                text="User B's review",
                visibility=Visibility.PRIVATE,
            )
            repo.save(review_b)
            db.commit()

            # Export for user A only
            use_case = ExportReviews(review_repository=repo)
            result = use_case.execute(user_a)

            assert len(result.reviews) == 1
            assert result.reviews[0].id == review_a.id
        finally:
            db.close()


class TestDeleteUserReviews:
    """Unit tests for DeleteUserReviews use case."""

    def _get_session(self):
        return TestSession()

    def test_delete_removes_all_user_reviews(self):
        """Delete removes both private and shared reviews for the user."""
        db = self._get_session()
        try:
            repo = SqlReviewRepository(db)
            user_id = uuid4()
            group_id = uuid4()

            # Create private review
            repo.save(
                Review(
                    user_id=user_id,
                    book_id=uuid4(),
                    rating=4,
                    text="Private",
                    visibility=Visibility.PRIVATE,
                )
            )

            # Create shared review
            repo.save(
                Review(
                    user_id=user_id,
                    book_id=uuid4(),
                    rating=5,
                    text="Shared",
                    visibility=Visibility.SHARED,
                    shared_with_type=SharedWithType.CLUB,
                    shared_with_id=group_id,
                )
            )
            db.commit()

            # Verify reviews exist
            assert len(repo.find_by_user_id(user_id)) == 2

            # Execute delete
            use_case = DeleteUserReviews(review_repository=repo)
            use_case.execute(user_id)
            db.commit()

            # Verify all reviews are deleted
            assert repo.find_by_user_id(user_id) == []
        finally:
            db.close()

    def test_delete_does_not_affect_other_users_reviews(self):
        """Delete only removes reviews belonging to the specified user."""
        db = self._get_session()
        try:
            repo = SqlReviewRepository(db)
            user_a = uuid4()
            user_b = uuid4()

            # User A's review
            repo.save(
                Review(
                    user_id=user_a,
                    book_id=uuid4(),
                    rating=3,
                    visibility=Visibility.PRIVATE,
                )
            )

            # User B's review
            repo.save(
                Review(
                    user_id=user_b,
                    book_id=uuid4(),
                    rating=4,
                    visibility=Visibility.PRIVATE,
                )
            )
            db.commit()

            # Delete user A's reviews
            use_case = DeleteUserReviews(review_repository=repo)
            use_case.execute(user_a)
            db.commit()

            # User A has no reviews
            assert repo.find_by_user_id(user_a) == []

            # User B still has their review
            assert len(repo.find_by_user_id(user_b)) == 1
        finally:
            db.close()

    def test_delete_is_idempotent_for_user_with_no_reviews(self):
        """Delete does not raise when user has no reviews."""
        db = self._get_session()
        try:
            repo = SqlReviewRepository(db)
            use_case = DeleteUserReviews(review_repository=repo)

            # Should not raise
            use_case.execute(uuid4())
            db.commit()
        finally:
            db.close()

    def test_after_deletion_reviews_not_found_by_id(self):
        """After deletion, individual reviews are not found by find_by_id."""
        db = self._get_session()
        try:
            repo = SqlReviewRepository(db)
            user_id = uuid4()

            review = Review(
                user_id=user_id,
                book_id=uuid4(),
                rating=5,
                text="Soon to be deleted",
                visibility=Visibility.PRIVATE,
            )
            repo.save(review)
            db.commit()

            # Verify review exists
            assert repo.find_by_id(review.id) is not None

            # Delete all user reviews
            use_case = DeleteUserReviews(review_repository=repo)
            use_case.execute(user_id)
            db.commit()

            # Verify review is gone
            assert repo.find_by_id(review.id) is None
        finally:
            db.close()
