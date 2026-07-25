"""Repository interfaces for the Reviews bounded context.

Reference: ADR-0017 (all dependencies behind abstractions)
"""

from typing import Protocol
from uuid import UUID

from app.reviews.domain.entities import Review


class ReviewRepository(Protocol):
    """Persistence interface for Review."""

    def save(self, review: Review) -> Review: ...

    def find_by_id(self, review_id: UUID) -> Review | None: ...

    def find_by_book_id(self, book_id: UUID) -> list[Review]: ...

    def find_by_user_id(self, user_id: UUID) -> list[Review]: ...

    def update(self, review: Review) -> Review: ...

    def delete(self, review_id: UUID) -> None: ...

    def delete_all_by_user_id(self, user_id: UUID) -> None: ...


class MembershipChecker(Protocol):
    """Checks user membership in groups and clubs.

    Used by ListReviews to verify access to shared reviews (Req 2.1, 2.3).
    Abstracts over the identity and community modules.
    """

    def is_member_of_group(self, user_id: UUID, group_id: UUID) -> bool:
        """Check if user is an active member of the family group."""
        ...

    def is_member_of_club(self, user_id: UUID, club_id: UUID) -> bool:
        """Check if user is a member of the club (via its parent group)."""
        ...
