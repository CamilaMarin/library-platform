"""CreateReview use case.

Creates a book review with explicit visibility control.
Reference: reviews/requirements.md Req 1.1, 1.2, 1.3, 1.5; ADR-0007
"""

from dataclasses import dataclass
from uuid import UUID

from app.reviews.application.protocols import ReviewRepository
from app.reviews.domain.entities import Review, SharedWithType, Visibility


@dataclass
class CreateReviewRequest:
    """Input for the CreateReview use case.

    visibility is required — never defaults to shared or public (Req 1.5).
    """

    user_id: UUID
    book_id: UUID
    rating: int
    visibility: Visibility
    text: str | None = None
    shared_with_type: SharedWithType | None = None
    shared_with_id: UUID | None = None


class InvalidVisibilityTargetError(Exception):
    """Raised when shared review lacks shared_with target."""

    pass


class CreateReview:
    """Use case: create a review with explicit visibility (ADR-0007)."""

    def __init__(self, review_repository: ReviewRepository):
        self._review_repo = review_repository

    def execute(self, request: CreateReviewRequest) -> Review:
        """Create a review enforcing visibility invariants.

        Raises:
            InvalidVisibilityTargetError: when visibility is 'shared' but
                shared_with_type or shared_with_id is missing.
            ValueError: when rating is out of range or invariants are violated.
        """
        # Enforce: shared visibility requires explicit target (Req 1.3)
        if request.visibility == Visibility.SHARED:
            if request.shared_with_type is None or request.shared_with_id is None:
                raise InvalidVisibilityTargetError(
                    "Shared review requires both shared_with_type and shared_with_id"
                )

        # Domain entity enforces all invariants in __post_init__
        review = Review(
            user_id=request.user_id,
            book_id=request.book_id,
            rating=request.rating,
            text=request.text,
            visibility=request.visibility,
            shared_with_type=request.shared_with_type,
            shared_with_id=request.shared_with_id,
        )

        return self._review_repo.save(review)
