"""Comprehensive domain + integration tests: visibility invariant, access control, privacy.

This file covers gap scenarios NOT already tested in existing test files:
- Dynamic membership: user leaves group → shared review becomes invisible (Property 3)
- End-to-end create + list with access control (Properties 3, 4, 5)
- Author sees own reviews but NOT another user's shared review in a non-member group

Coverage map for design.md correctness properties:
- Property 1 (private → null shared_with): test_review_entity.py, test_create_review_integration.py
- Property 2 (shared → non-null shared_with): test_review_entity.py, test_create_review_integration.py
- Property 3 (shared → only group/club members): test_list_reviews_integration.py + THIS FILE
- Property 4 (private → only author): test_list_reviews_integration.py + THIS FILE
- Property 5 (mandatory access check): test_list_reviews_integration.py + THIS FILE
- Privacy (export/delete): test_reviews_privacy.py

Reference: reviews/design.md, requirements.md Req 1, 2
"""

from uuid import uuid4

import pytest

from app.reviews.application.list_reviews import ListReviews, ListReviewsRequest
from app.reviews.domain.entities import Review, SharedWithType, Visibility


# --- In-memory test doubles ---


class InMemoryReviewRepository:
    """In-memory review repository for unit/domain tests."""

    def __init__(self):
        self.reviews: dict = {}

    def save(self, review: Review) -> Review:
        self.reviews[review.id] = review
        return review

    def find_by_id(self, review_id):
        return self.reviews.get(review_id)

    def find_by_book_id(self, book_id):
        return [r for r in self.reviews.values() if r.book_id == book_id]

    def find_by_user_id(self, user_id):
        return [r for r in self.reviews.values() if r.user_id == user_id]

    def update(self, review: Review) -> Review:
        self.reviews[review.id] = review
        return review

    def delete(self, review_id) -> None:
        self.reviews.pop(review_id, None)

    def delete_all_by_user_id(self, user_id) -> None:
        to_delete = [rid for rid, r in self.reviews.items() if r.user_id == user_id]
        for rid in to_delete:
            del self.reviews[rid]


class FakeMembershipChecker:
    """Configurable membership checker that supports dynamic membership changes."""

    def __init__(self):
        self.group_memberships: set[tuple] = set()
        self.club_memberships: set[tuple] = set()

    def add_group_member(self, user_id, group_id):
        self.group_memberships.add((user_id, group_id))

    def remove_group_member(self, user_id, group_id):
        self.group_memberships.discard((user_id, group_id))

    def add_club_member(self, user_id, club_id):
        self.club_memberships.add((user_id, club_id))

    def remove_club_member(self, user_id, club_id):
        self.club_memberships.discard((user_id, club_id))

    def is_member_of_group(self, user_id, group_id) -> bool:
        return (user_id, group_id) in self.group_memberships

    def is_member_of_club(self, user_id, club_id) -> bool:
        return (user_id, club_id) in self.club_memberships


# --- Dynamic Membership Tests (Property 3) ---


class TestDynamicMembershipAccessControl:
    """Property 3: Access control is evaluated at query time.

    When a user leaves a group, previously-visible shared reviews
    in that group become invisible to them.
    """

    def _setup(self):
        repo = InMemoryReviewRepository()
        checker = FakeMembershipChecker()
        uc = ListReviews(review_repository=repo, membership_checker=checker)
        return repo, checker, uc

    def test_user_leaves_group_loses_access_to_shared_review(self):
        """Property 3: User who leaves a group no longer sees shared reviews."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        member_id = uuid4()
        group_id = uuid4()
        book_id = uuid4()

        # Author shares a review with the group
        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=5,
            text="Shared with the group",
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        repo.save(review)

        # User is initially a member → sees the review
        checker.add_group_member(member_id, group_id)
        result_before = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member_id)
        )
        assert len(result_before) == 1
        assert result_before[0].id == review.id

        # User leaves the group → no longer sees the review
        checker.remove_group_member(member_id, group_id)
        result_after = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member_id)
        )
        assert len(result_after) == 0

    def test_user_leaves_club_loses_access_to_shared_review(self):
        """Property 3: User who leaves a club no longer sees club-shared reviews."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        member_id = uuid4()
        club_id = uuid4()
        book_id = uuid4()

        # Author shares a review with the club
        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=4,
            text="For the book club",
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.CLUB,
            shared_with_id=club_id,
        )
        repo.save(review)

        # User is initially a club member → sees the review
        checker.add_club_member(member_id, club_id)
        result_before = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member_id)
        )
        assert len(result_before) == 1

        # User leaves the club → no longer sees the review
        checker.remove_club_member(member_id, club_id)
        result_after = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member_id)
        )
        assert len(result_after) == 0

    def test_author_still_sees_own_review_after_leaving_group(self):
        """Author always sees own reviews even after leaving the target group."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        group_id = uuid4()
        book_id = uuid4()

        # Author creates review shared with their own group, is a member
        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=3,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        repo.save(review)
        checker.add_group_member(author_id, group_id)

        # Author sees their own review
        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=author_id)
        )
        assert len(result) == 1

        # Author leaves the group — still sees own review (author access)
        checker.remove_group_member(author_id, group_id)
        result_after = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=author_id)
        )
        assert len(result_after) == 1
        assert result_after[0].id == review.id

    def test_multiple_reviews_dynamic_access(self):
        """Multiple shared reviews from different groups — membership changes affect only relevant ones."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        member_id = uuid4()
        group_a = uuid4()
        group_b = uuid4()
        book_id = uuid4()

        # Review shared with group A
        review_a = Review(
            user_id=author_id,
            book_id=book_id,
            rating=5,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_a,
        )
        repo.save(review_a)

        # Review shared with group B
        review_b = Review(
            user_id=author_id,
            book_id=book_id,
            rating=3,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_b,
        )
        repo.save(review_b)

        # Member is in both groups
        checker.add_group_member(member_id, group_a)
        checker.add_group_member(member_id, group_b)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member_id)
        )
        assert len(result) == 2

        # Member leaves group A — only sees group B review
        checker.remove_group_member(member_id, group_a)
        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member_id)
        )
        assert len(result) == 1
        assert result[0].id == review_b.id


# --- End-to-End Access Control Tests (Properties 3, 4, 5) ---


class TestEndToEndAccessControl:
    """End-to-end tests combining create + list with access control.

    Verifies Property 5: no review is served without explicit access check.
    """

    def _setup(self):
        repo = InMemoryReviewRepository()
        checker = FakeMembershipChecker()
        uc = ListReviews(review_repository=repo, membership_checker=checker)
        return repo, checker, uc

    def test_author_sees_own_private_non_member_of_shared(self):
        """User sees own private reviews but NOT another user's shared review in non-member group."""
        repo, checker, uc = self._setup()
        user_a = uuid4()
        user_b = uuid4()
        group_id = uuid4()
        book_id = uuid4()

        # User A has a private review
        own_review = Review(
            user_id=user_a,
            book_id=book_id,
            rating=4,
            visibility=Visibility.PRIVATE,
            text="My private review",
        )
        repo.save(own_review)

        # User B shared a review with a group User A is NOT in
        shared_review = Review(
            user_id=user_b,
            book_id=book_id,
            rating=5,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        repo.save(shared_review)

        # User A queries — sees own review, not the shared one
        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=user_a)
        )
        assert len(result) == 1
        assert result[0].id == own_review.id

    def test_user_with_no_reviews_and_no_memberships_sees_nothing(self):
        """Property 5: A user with no connection to any reviews sees empty."""
        repo, checker, uc = self._setup()
        author = uuid4()
        outsider = uuid4()
        group_id = uuid4()
        book_id = uuid4()

        # Private review by author
        repo.save(
            Review(
                user_id=author,
                book_id=book_id,
                rating=4,
                visibility=Visibility.PRIVATE,
            )
        )

        # Shared review by author
        repo.save(
            Review(
                user_id=author,
                book_id=book_id,
                rating=5,
                visibility=Visibility.SHARED,
                shared_with_type=SharedWithType.GROUP,
                shared_with_id=group_id,
            )
        )

        # Outsider sees nothing
        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=outsider)
        )
        assert result == []

    def test_membership_grants_access_to_shared_not_private(self):
        """Property 5: Membership in a group grants access to shared reviews only, never private."""
        repo, checker, uc = self._setup()
        author = uuid4()
        member = uuid4()
        group_id = uuid4()
        book_id = uuid4()

        # Author has both private and shared reviews on same book
        private = Review(
            user_id=author,
            book_id=book_id,
            rating=2,
            visibility=Visibility.PRIVATE,
            text="Secret thoughts",
        )
        repo.save(private)

        shared = Review(
            user_id=author,
            book_id=book_id,
            rating=4,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
            text="For the group",
        )
        repo.save(shared)

        # Member of the group
        checker.add_group_member(member, group_id)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member)
        )

        # Member sees shared review but NOT private
        assert len(result) == 1
        assert result[0].id == shared.id
        assert result[0].visibility == Visibility.SHARED


# --- Integration test: dynamic membership with SQL (full stack) ---


class TestDynamicMembershipIntegration:
    """Full-stack integration test: user leaves group → loses access via SQL layer.

    Uses actual database via TestSession to verify the membership check
    is evaluated at query time (not cached at review creation time).
    """

    def _get_auth_header(self, user_id=None):
        """Create a valid auth token for testing."""
        from app.auth.jwt import create_access_token

        uid = user_id or uuid4()
        token = create_access_token(str(uid))
        return {"Authorization": f"Bearer {token}"}, uid

    def _create_review_via_api(self, client, headers, **kwargs):
        """Helper to create a review via the API."""
        body = {
            "book_id": str(kwargs.get("book_id", uuid4())),
            "rating": kwargs.get("rating", 3),
            "visibility": kwargs.get("visibility", "private"),
        }
        if kwargs.get("text"):
            body["text"] = kwargs["text"]
        if kwargs.get("shared_with_type"):
            body["shared_with_type"] = kwargs["shared_with_type"]
        if kwargs.get("shared_with_id"):
            body["shared_with_id"] = str(kwargs["shared_with_id"])
        response = client.post("/reviews/", json=body, headers=headers)
        assert response.status_code == 201
        return response.json()

    def test_user_leaves_group_review_becomes_invisible_sql(self):
        """Property 3 (integration): membership change at DB level removes access."""
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session

        from app.database import get_db
        from app.identity.infrastructure.models import (
            FamilyGroupModel,
            GroupMembershipModel,
        )
        from app.main import app

        client = TestClient(app)
        author_headers, author_id = self._get_auth_header()
        member_headers, member_id = self._get_auth_header()

        group_id = uuid4()
        book_id = uuid4()

        # Set up group + membership
        db: Session = next(app.dependency_overrides[get_db]())
        db.add(FamilyGroupModel(id=group_id, name="Dynamic Group"))
        membership = GroupMembershipModel(
            id=uuid4(),
            group_id=group_id,
            user_id=member_id,
            status="accepted",
        )
        db.add(membership)
        db.commit()

        # Author creates shared review
        self._create_review_via_api(
            client,
            author_headers,
            book_id=book_id,
            visibility="shared",
            shared_with_type="group",
            shared_with_id=group_id,
            rating=5,
        )

        # Member sees the review (active membership)
        response = client.get(f"/books/{book_id}/reviews", headers=member_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Member leaves the group (status changed to "rejected")
        membership.status = "rejected"
        db.commit()

        # Member no longer sees the review
        response = client.get(f"/books/{book_id}/reviews", headers=member_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_user_leaves_club_review_becomes_invisible_sql(self):
        """Property 3 (integration): club membership revocation removes access."""
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session

        from app.community.infrastructure.models import ClubModel
        from app.database import get_db
        from app.identity.infrastructure.models import (
            FamilyGroupModel,
            GroupMembershipModel,
        )
        from app.main import app

        client = TestClient(app)
        author_headers, author_id = self._get_auth_header()
        member_headers, member_id = self._get_auth_header()

        group_id = uuid4()
        club_id = uuid4()
        book_id = uuid4()

        # Set up group + club + membership
        db: Session = next(app.dependency_overrides[get_db]())
        db.add(FamilyGroupModel(id=group_id, name="Club Family"))
        db.add(ClubModel(id=club_id, group_id=group_id, name="Reading Club"))
        membership = GroupMembershipModel(
            id=uuid4(),
            group_id=group_id,
            user_id=member_id,
            status="accepted",
        )
        db.add(membership)
        db.commit()

        # Author creates review shared with club
        self._create_review_via_api(
            client,
            author_headers,
            book_id=book_id,
            visibility="shared",
            shared_with_type="club",
            shared_with_id=club_id,
            rating=4,
        )

        # Member sees the review
        response = client.get(f"/books/{book_id}/reviews", headers=member_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Member leaves (membership revoked)
        membership.status = "rejected"
        db.commit()

        # Member no longer sees the review
        response = client.get(f"/books/{book_id}/reviews", headers=member_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_end_to_end_create_and_list_access_control(self):
        """End-to-end: create multiple reviews → list shows only authorized ones.

        Properties 3, 4, 5: comprehensive scenario with multiple users and visibilities.
        """
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session

        from app.database import get_db
        from app.identity.infrastructure.models import (
            FamilyGroupModel,
            GroupMembershipModel,
        )
        from app.main import app

        client = TestClient(app)
        author_headers, author_id = self._get_auth_header()
        member_headers, member_id = self._get_auth_header()
        outsider_headers, outsider_id = self._get_auth_header()

        group_id = uuid4()
        book_id = uuid4()

        # Set up group — member is in it, outsider is not
        db: Session = next(app.dependency_overrides[get_db]())
        db.add(FamilyGroupModel(id=group_id, name="Family A"))
        db.add(
            GroupMembershipModel(
                id=uuid4(),
                group_id=group_id,
                user_id=member_id,
                status="accepted",
            )
        )
        db.commit()

        # Author creates a private review
        self._create_review_via_api(
            client,
            author_headers,
            book_id=book_id,
            visibility="private",
            rating=2,
            text="Private thoughts",
        )

        # Author creates a shared review with the group
        self._create_review_via_api(
            client,
            author_headers,
            book_id=book_id,
            visibility="shared",
            shared_with_type="group",
            shared_with_id=group_id,
            rating=5,
            text="For the family",
        )

        # Author sees both own reviews
        response = client.get(f"/books/{book_id}/reviews", headers=author_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Member sees only the shared review (not the private one)
        response = client.get(f"/books/{book_id}/reviews", headers=member_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["visibility"] == "shared"
        assert data[0]["text"] == "For the family"

        # Outsider sees nothing
        response = client.get(f"/books/{book_id}/reviews", headers=outsider_headers)
        assert response.status_code == 200
        assert response.json() == []
