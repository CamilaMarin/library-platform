"""DeleteReview use case.

Allows the author to delete their own review.
Reference: reviews/requirements.md Req 1.4
"""

from dataclasses import dataclass
from uuid import UUID

from app.reviews.application.edit_review import ForbiddenError, ReviewNotFoundError
from app.reviews.application.protocols import ReviewRepository


@dataclass
class DeleteReviewRequest:
    """Input for the DeleteReview use case."""

    review_id: UUID
    user_id: UUID


class DeleteReview:
    """Use case: delete a review (author-only, Req 1.4)."""

    def __init__(self, review_repository: ReviewRepository):
        self._review_repo = review_repository

    def execute(self, request: DeleteReviewRequest) -> None:
        """Delete a review enforcing author-only access.

        Raises:
            ReviewNotFoundError: when review_id does not exist.
            ForbiddenError: when user_id is not the review author.
        """
        review = self._review_repo.find_by_id(request.review_id)
        if review is None:
            raise ReviewNotFoundError(f"Review {request.review_id} not found")

        # Author-only check (Req 1.4)
        if review.user_id != request.user_id:
            raise ForbiddenError("Only the author can delete this review")

        self._review_repo.delete(request.review_id)
