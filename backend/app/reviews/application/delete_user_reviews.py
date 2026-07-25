"""DeleteUserReviews use case — permanently deletes all reviews owned by a user.

Integrates with the Privacy module's ARCO (cancellation) right.
MVP: hard-delete, no recovery period.

Reference: reviews/requirements.md Req 2.3, ADR-0003
"""

from uuid import UUID

from app.reviews.application.protocols import ReviewRepository


class DeleteUserReviews:
    """Use case: permanently delete all reviews owned by a user (account cancellation).

    Called when a user exercises their cancellation right (ARCO).
    Deletes ALL reviews — both private and shared — since reviews
    are personal data (ADR-0003).
    """

    def __init__(self, review_repository: ReviewRepository):
        self._review_repo = review_repository

    def execute(self, user_id: UUID) -> None:
        """Delete all reviews for the given user."""
        self._review_repo.delete_all_by_user_id(user_id)
