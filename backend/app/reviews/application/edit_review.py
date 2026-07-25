"""EditReview use case.

Allows the author to update their own review while maintaining visibility invariants.
Reference: reviews/requirements.md Req 1.4; ADR-0007
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from app.reviews.application.protocols import ReviewRepository
from app.reviews.domain.entities import Review, SharedWithType, Visibility


class ForbiddenError(Exception):
    """Raised when a non-author attempts to edit or delete a review."""

    pass


class ReviewNotFoundError(Exception):
    """Raised when the review does not exist."""

    pass


@dataclass
class EditReviewRequest:
    """Input for the EditReview use case.

    All fields except review_id and user_id are optional — partial updates.
    """

    review_id: UUID
    user_id: UUID
    rating: int | None = None
    text: str | None = None
    visibility: Visibility | None = None
    shared_with_type: SharedWithType | None = None
    shared_with_id: UUID | None = None
    # Sentinel to distinguish "not provided" from "set to None"
    clear_text: bool = False


class EditReview:
    """Use case: edit a review (author-only, Req 1.4)."""

    def __init__(self, review_repository: ReviewRepository):
        self._review_repo = review_repository

    def execute(self, request: EditReviewRequest) -> Review:
        """Edit a review enforcing author-only access and visibility invariants.

        Raises:
            ReviewNotFoundError: when review_id does not exist.
            ForbiddenError: when user_id is not the review author.
            ValueError: when visibility invariants are violated after update.
        """
        review = self._review_repo.find_by_id(request.review_id)
        if review is None:
            raise ReviewNotFoundError(f"Review {request.review_id} not found")

        # Author-only check (Req 1.4)
        if review.user_id != request.user_id:
            raise ForbiddenError("Only the author can edit this review")

        # Apply partial updates
        new_rating = request.rating if request.rating is not None else review.rating
        new_text = None if request.clear_text else (request.text if request.text is not None else review.text)
        new_visibility = request.visibility if request.visibility is not None else review.visibility
        new_shared_with_type = request.shared_with_type if request.visibility is not None else review.shared_with_type
        new_shared_with_id = request.shared_with_id if request.visibility is not None else review.shared_with_id

        # Reconstruct with updated fields — domain entity validates invariants
        updated_review = Review(
            id=review.id,
            user_id=review.user_id,
            book_id=review.book_id,
            rating=new_rating,
            text=new_text,
            visibility=new_visibility,
            shared_with_type=new_shared_with_type,
            shared_with_id=new_shared_with_id,
            created_at=review.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        return self._review_repo.update(updated_review)
