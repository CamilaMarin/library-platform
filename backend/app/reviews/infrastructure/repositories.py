"""Repository implementations for the Reviews bounded context.

Implements protocols from application/protocols.py.
Reference: ADR-0017, ADR-0007
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.reviews.domain.entities import Review, SharedWithType, Visibility
from app.reviews.infrastructure.models import ReviewModel


class SqlReviewRepository:
    """SQLAlchemy implementation of ReviewRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, review: Review) -> Review:
        model = ReviewModel(
            id=review.id,
            user_id=review.user_id,
            book_id=review.book_id,
            rating=review.rating,
            text=review.text,
            visibility=review.visibility.value,
            shared_with_type=(
                review.shared_with_type.value if review.shared_with_type else None
            ),
            shared_with_id=review.shared_with_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
        self._session.add(model)
        self._session.flush()
        return review

    def find_by_id(self, review_id: UUID) -> Review | None:
        model = self._session.get(ReviewModel, review_id)
        if not model:
            return None
        return self._to_domain(model)

    def find_by_book_id(self, book_id: UUID) -> list[Review]:
        models = (
            self._session.query(ReviewModel)
            .filter(ReviewModel.book_id == book_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def update(self, review: Review) -> Review:
        model = self._session.get(ReviewModel, review.id)
        if not model:
            raise ValueError(f"Review {review.id} not found")
        model.rating = review.rating
        model.text = review.text
        model.visibility = review.visibility.value
        model.shared_with_type = (
            review.shared_with_type.value if review.shared_with_type else None
        )
        model.shared_with_id = review.shared_with_id
        model.updated_at = review.updated_at
        self._session.flush()
        return review

    def find_by_user_id(self, user_id: UUID) -> list[Review]:
        models = (
            self._session.query(ReviewModel)
            .filter(ReviewModel.user_id == user_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def delete(self, review_id: UUID) -> None:
        model = self._session.get(ReviewModel, review_id)
        if model:
            self._session.delete(model)
            self._session.flush()

    def delete_all_by_user_id(self, user_id: UUID) -> None:
        self._session.query(ReviewModel).filter(
            ReviewModel.user_id == user_id
        ).delete()
        self._session.flush()

    def _to_domain(self, model: ReviewModel) -> Review:
        return Review(
            id=model.id,
            user_id=model.user_id,
            book_id=model.book_id,
            rating=model.rating,
            text=model.text,
            visibility=Visibility(model.visibility),
            shared_with_type=(
                SharedWithType(model.shared_with_type)
                if model.shared_with_type
                else None
            ),
            shared_with_id=model.shared_with_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
