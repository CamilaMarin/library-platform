"""ListReviews use case.

Returns only reviews the requester is authorized to see.
Access control logic (Req 2.1, 2.2, 2.3):
- Author always sees their own reviews regardless of visibility.
- Shared reviews are only visible to members of the target group/club.
- No review is ever served without an explicit access check (Property 5).

Reference: reviews/design.md, ADR-0007
"""

from dataclasses import dataclass
from uuid import UUID

from app.reviews.application.protocols import MembershipChecker, ReviewRepository
from app.reviews.domain.entities import Review, SharedWithType, Visibility


@dataclass
class ListReviewsRequest:
    """Input for the ListReviews use case."""

    book_id: UUID
    requester_user_id: UUID


class ListReviews:
    """Use case: list reviews for a book filtered by access control.

    Implements Properties 3, 4, 5 from design.md:
    - Property 3: shared review only served to group/club members.
    - Property 4: private review only served to author.
    - Property 5: every review passes an explicit access check.
    """

    def __init__(
        self,
        review_repository: ReviewRepository,
        membership_checker: MembershipChecker,
    ):
        self._review_repo = review_repository
        self._membership_checker = membership_checker

    def execute(self, request: ListReviewsRequest) -> list[Review]:
        """Return only reviews the requester is authorized to see."""
        all_reviews = self._review_repo.find_by_book_id(request.book_id)
        visible: list[Review] = []

        for review in all_reviews:
            if self._is_visible_to(review, request.requester_user_id):
                visible.append(review)

        return visible

    def _is_visible_to(self, review: Review, requester_id: UUID) -> bool:
        """Explicit access check for a single review (Property 5).

        Rules:
        - Author always sees their own reviews (any visibility).
        - Private reviews are only visible to the author (Property 4).
        - Shared reviews require membership in the target entity (Property 3).
        """
        # Author always sees their own reviews
        if review.user_id == requester_id:
            return True

        # Private reviews: only the author (already handled above)
        if review.visibility == Visibility.PRIVATE:
            return False

        # Shared reviews: check membership in target entity
        if review.visibility == Visibility.SHARED:
            if review.shared_with_type == SharedWithType.GROUP:
                return self._membership_checker.is_member_of_group(
                    requester_id, review.shared_with_id
                )
            elif review.shared_with_type == SharedWithType.CLUB:
                return self._membership_checker.is_member_of_club(
                    requester_id, review.shared_with_id
                )

        return False
