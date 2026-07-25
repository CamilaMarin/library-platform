"""ExportReviews use case — exports all reviews owned by a user.

Integrates with the Privacy module's ARCO (access) right.
Reviews are personal data (ADR-0003) — export includes ALL review data
regardless of visibility (private and shared).

Reference: reviews/requirements.md Req 2.3, ADR-0003
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.reviews.application.protocols import ReviewRepository


@dataclass
class ExportedReview:
    """Exported review record for ARCO data access."""

    id: UUID
    book_id: UUID
    rating: int
    text: str | None
    visibility: str
    shared_with_type: str | None
    shared_with_id: UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass
class ReviewExportResult:
    """Structured export of all reviews owned by a user."""

    reviews: list[ExportedReview]


class ExportReviews:
    """Use case: export all reviews owned by a user (ARCO access right).

    Returns ALL reviews by the user — both private and shared —
    since reviews are personal data regardless of visibility.
    """

    def __init__(self, review_repository: ReviewRepository):
        self._review_repo = review_repository

    def execute(self, user_id: UUID) -> ReviewExportResult:
        """Export all reviews for the given user."""
        reviews = self._review_repo.find_by_user_id(user_id)

        return ReviewExportResult(
            reviews=[
                ExportedReview(
                    id=r.id,
                    book_id=r.book_id,
                    rating=r.rating,
                    text=r.text,
                    visibility=r.visibility.value,
                    shared_with_type=(
                        r.shared_with_type.value if r.shared_with_type else None
                    ),
                    shared_with_id=r.shared_with_id,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
                for r in reviews
            ],
        )
