"""Reviews REST endpoints.

Reference: reviews/tasks.md#2, #3, #4, ADR-0007, requirements.md Req 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.interface.dependencies import get_current_user_id
from app.reviews.application.create_review import (
    CreateReview,
    CreateReviewRequest as CreateReviewInput,
    InvalidVisibilityTargetError,
)
from app.reviews.application.delete_review import DeleteReview, DeleteReviewRequest
from app.reviews.application.edit_review import (
    EditReview,
    EditReviewRequest,
    ForbiddenError,
    ReviewNotFoundError,
)
from app.reviews.application.list_reviews import ListReviews, ListReviewsRequest
from app.reviews.infrastructure.membership_checker import SqlMembershipChecker
from app.reviews.infrastructure.repositories import SqlReviewRepository
from app.reviews.interface.schemas import (
    CreateReviewRequest,
    ReviewResponse,
    UpdateReviewRequest,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])
books_reviews_router = APIRouter(prefix="/books", tags=["reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    request: CreateReviewRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new review with explicit visibility choice.

    Visibility must always be explicitly provided (Req 1.5).
    When visibility is 'shared', shared_with_type and shared_with_id are required (Req 1.3).
    """
    repo = SqlReviewRepository(db)
    use_case = CreateReview(review_repository=repo)

    try:
        review = use_case.execute(
            CreateReviewInput(
                user_id=user_id,
                book_id=request.book_id,
                rating=request.rating,
                visibility=request.visibility,
                text=request.text,
                shared_with_type=request.shared_with_type,
                shared_with_id=request.shared_with_id,
            )
        )
    except InvalidVisibilityTargetError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_visibility_target",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    db.commit()

    return ReviewResponse(
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


@router.patch("/{review_id}", response_model=ReviewResponse)
def edit_review(
    review_id: UUID,
    request: UpdateReviewRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Edit an existing review (author-only, Req 1.4).

    Accepts partial updates. Visibility invariants are enforced.
    Returns 403 if the requester is not the author.
    Returns 404 if the review does not exist.
    """
    repo = SqlReviewRepository(db)
    use_case = EditReview(review_repository=repo)

    try:
        review = use_case.execute(
            EditReviewRequest(
                review_id=review_id,
                user_id=user_id,
                rating=request.rating,
                text=request.text,
                visibility=request.visibility,
                shared_with_type=request.shared_with_type,
                shared_with_id=request.shared_with_id,
            )
        )
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="review_not_found",
        )
    except ForbiddenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    db.commit()

    return ReviewResponse(
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


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a review (author-only, Req 1.4).

    Returns 204 No Content on success.
    Returns 403 if the requester is not the author.
    Returns 404 if the review does not exist.
    """
    repo = SqlReviewRepository(db)
    use_case = DeleteReview(review_repository=repo)

    try:
        use_case.execute(
            DeleteReviewRequest(
                review_id=review_id,
                user_id=user_id,
            )
        )
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="review_not_found",
        )
    except ForbiddenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden",
        )

    db.commit()


@books_reviews_router.get(
    "/{book_id}/reviews",
    response_model=list[ReviewResponse],
)
def list_book_reviews(
    book_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List reviews for a book filtered by access control.

    Returns only reviews the requester is authorized to see (Req 2.1, 2.2, 2.3):
    - Author's own reviews (any visibility)
    - Shared reviews where requester is a member of the target group/club

    If the requester has no access to any shared reviews, returns only their own
    private reviews (empty shared set, not an error).
    """
    repo = SqlReviewRepository(db)
    membership_checker = SqlMembershipChecker(db)
    use_case = ListReviews(
        review_repository=repo,
        membership_checker=membership_checker,
    )

    reviews = use_case.execute(
        ListReviewsRequest(
            book_id=book_id,
            requester_user_id=user_id,
        )
    )

    return [
        ReviewResponse(
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
        for review in reviews
    ]
