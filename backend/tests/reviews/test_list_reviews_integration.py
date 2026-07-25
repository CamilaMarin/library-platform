"""Integration tests for ListReviews use case + GET /books/{book_id}/reviews endpoint.

Tests access control filtering (Req 2.1, 2.2, 2.3):
- Author sees their own private reviews
- Group member sees shared-with-group reviews
- Club member sees shared-with-club reviews
- Non-member does NOT see shared reviews
- User sees their own reviews regardless of visibility

Reference: reviews/design.md Properties 3, 4, 5; ADR-0007
"""

from uuid import uuid4

import pytest

from app.reviews.application.list_reviews import ListReviews, ListReviewsRequest
from app.reviews.domain.entities import Review, SharedWithType, Visibility


# --- In-memory test doubles ---


class InMemoryReviewRepository:
    def __init__(self):
        self.reviews: dict = {}

    def save(self, review: Review) -> Review:
        self.reviews[review.id] = review
        return review

    def find_by_id(self, review_id):
        return self.reviews.get(review_id)

    def find_by_book_id(self, book_id):
        return [r for r in self.reviews.values() if r.book_id == book_id]

    def update(self, review: Review) -> Review:
        self.reviews[review.id] = review
        return review

    def delete(self, review_id) -> None:
        self.reviews.pop(review_id, None)


class FakeMembershipChecker:
    """Configurable membership checker for testing."""

    def __init__(self):
        self.group_memberships: set[tuple] = set()
        self.club_memberships: set[tuple] = set()

    def add_group_member(self, user_id, group_id):
        self.group_memberships.add((user_id, group_id))

    def add_club_member(self, user_id, club_id):
        self.club_memberships.add((user_id, club_id))

    def is_member_of_group(self, user_id, group_id) -> bool:
        return (user_id, group_id) in self.group_memberships

    def is_member_of_club(self, user_id, club_id) -> bool:
        return (user_id, club_id) in self.club_memberships


# --- ListReviews use case unit tests ---


class TestListReviewsUseCase:
    """Unit tests for ListReviews access control logic."""

    def _setup(self):
        repo = InMemoryReviewRepository()
        checker = FakeMembershipChecker()
        uc = ListReviews(review_repository=repo, membership_checker=checker)
        return repo, checker, uc

    def test_author_sees_own_private_review(self):
        """Property 4: Author always sees their own private review."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        book_id = uuid4()

        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=4,
            visibility=Visibility.PRIVATE,
        )
        repo.save(review)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=author_id)
        )

        assert len(result) == 1
        assert result[0].id == review.id

    def test_other_user_cannot_see_private_review(self):
        """Property 4: Private review not served to non-author."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        other_id = uuid4()
        book_id = uuid4()

        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=4,
            visibility=Visibility.PRIVATE,
        )
        repo.save(review)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=other_id)
        )

        assert len(result) == 0

    def test_group_member_sees_shared_review(self):
        """Property 3 / Req 2.1: Group member sees shared-with-group review."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        member_id = uuid4()
        group_id = uuid4()
        book_id = uuid4()

        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=5,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        repo.save(review)
        checker.add_group_member(member_id, group_id)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member_id)
        )

        assert len(result) == 1
        assert result[0].id == review.id

    def test_non_group_member_cannot_see_shared_review(self):
        """Req 2.1: Non-member does NOT see shared-with-group review."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        non_member_id = uuid4()
        group_id = uuid4()
        book_id = uuid4()

        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=5,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        repo.save(review)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=non_member_id)
        )

        assert len(result) == 0

    def test_club_member_sees_shared_review(self):
        """Property 3 / Req 2.1: Club member sees shared-with-club review."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        member_id = uuid4()
        club_id = uuid4()
        book_id = uuid4()

        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=3,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.CLUB,
            shared_with_id=club_id,
        )
        repo.save(review)
        checker.add_club_member(member_id, club_id)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=member_id)
        )

        assert len(result) == 1
        assert result[0].id == review.id

    def test_non_club_member_cannot_see_shared_review(self):
        """Req 2.1: Non-member does NOT see shared-with-club review."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        non_member_id = uuid4()
        club_id = uuid4()
        book_id = uuid4()

        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=3,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.CLUB,
            shared_with_id=club_id,
        )
        repo.save(review)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=non_member_id)
        )

        assert len(result) == 0

    def test_author_sees_own_shared_review_without_membership(self):
        """Author always sees their own reviews regardless of visibility."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        group_id = uuid4()
        book_id = uuid4()

        review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=4,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        repo.save(review)
        # Note: author is NOT added as group member — still sees own review

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=author_id)
        )

        assert len(result) == 1
        assert result[0].id == review.id

    def test_no_reviews_for_book_returns_empty(self):
        """Empty book returns empty list, not an error."""
        repo, checker, uc = self._setup()
        requester_id = uuid4()
        book_id = uuid4()

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=requester_id)
        )

        assert result == []

    def test_mixed_visibility_filtering(self):
        """Complex scenario: only authorized reviews are returned."""
        repo, checker, uc = self._setup()
        author_id = uuid4()
        requester_id = uuid4()
        group_id = uuid4()
        other_group_id = uuid4()
        book_id = uuid4()

        # Author's private review — requester should NOT see
        private_review = Review(
            user_id=author_id,
            book_id=book_id,
            rating=2,
            visibility=Visibility.PRIVATE,
        )
        repo.save(private_review)

        # Shared with group requester IS a member of
        shared_visible = Review(
            user_id=author_id,
            book_id=book_id,
            rating=5,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        repo.save(shared_visible)

        # Shared with a different group requester is NOT a member of
        shared_hidden = Review(
            user_id=author_id,
            book_id=book_id,
            rating=1,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=other_group_id,
        )
        repo.save(shared_hidden)

        # Requester's own private review
        own_review = Review(
            user_id=requester_id,
            book_id=book_id,
            rating=3,
            visibility=Visibility.PRIVATE,
        )
        repo.save(own_review)

        checker.add_group_member(requester_id, group_id)

        result = uc.execute(
            ListReviewsRequest(book_id=book_id, requester_user_id=requester_id)
        )

        result_ids = {r.id for r in result}
        assert shared_visible.id in result_ids
        assert own_review.id in result_ids
        assert private_review.id not in result_ids
        assert shared_hidden.id not in result_ids
        assert len(result) == 2


# --- Endpoint integration tests ---


class TestListBookReviewsEndpoint:
    """Integration tests for GET /books/{book_id}/reviews via TestClient."""

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

    def test_author_sees_own_private_review(self):
        """Req 2.2: Author sees their own private review."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        book_id = uuid4()

        self._create_review_via_api(
            client, headers, book_id=book_id, visibility="private", rating=4
        )

        response = client.get(f"/books/{book_id}/reviews", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["rating"] == 4
        assert data[0]["user_id"] == str(user_id)

    def test_other_user_cannot_see_private_review(self):
        """Req 2.2: Private review invisible to non-author."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        author_headers, author_id = self._get_auth_header()
        other_headers, other_id = self._get_auth_header()
        book_id = uuid4()

        self._create_review_via_api(
            client, author_headers, book_id=book_id, visibility="private"
        )

        response = client.get(f"/books/{book_id}/reviews", headers=other_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_group_member_sees_shared_review(self):
        """Req 2.1: Group member sees shared-with-group review."""
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

        # Set up group + membership in DB
        group_id = uuid4()
        book_id = uuid4()

        db: Session = next(app.dependency_overrides[get_db]())
        db.add(FamilyGroupModel(id=group_id, name="Test Family"))
        db.add(
            GroupMembershipModel(
                id=uuid4(),
                group_id=group_id,
                user_id=member_id,
                status="accepted",
            )
        )
        db.commit()

        # Create shared review
        self._create_review_via_api(
            client,
            author_headers,
            book_id=book_id,
            visibility="shared",
            shared_with_type="group",
            shared_with_id=group_id,
        )

        # Member should see it
        response = client.get(f"/books/{book_id}/reviews", headers=member_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["visibility"] == "shared"
        assert data[0]["shared_with_id"] == str(group_id)

    def test_non_member_cannot_see_shared_review(self):
        """Req 2.1: Non-member does NOT see shared reviews."""
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session

        from app.database import get_db
        from app.identity.infrastructure.models import FamilyGroupModel
        from app.main import app

        client = TestClient(app)
        author_headers, author_id = self._get_auth_header()
        outsider_headers, outsider_id = self._get_auth_header()

        group_id = uuid4()
        book_id = uuid4()

        db: Session = next(app.dependency_overrides[get_db]())
        db.add(FamilyGroupModel(id=group_id, name="Private Family"))
        db.commit()

        # Create shared review with a group the outsider is not a member of
        self._create_review_via_api(
            client,
            author_headers,
            book_id=book_id,
            visibility="shared",
            shared_with_type="group",
            shared_with_id=group_id,
        )

        # Outsider should NOT see it
        response = client.get(f"/books/{book_id}/reviews", headers=outsider_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_club_member_sees_shared_review(self):
        """Req 2.1: Club member sees shared-with-club review."""
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

        db: Session = next(app.dependency_overrides[get_db]())
        db.add(FamilyGroupModel(id=group_id, name="Club Family"))
        db.add(ClubModel(id=club_id, group_id=group_id, name="Book Club"))
        db.add(
            GroupMembershipModel(
                id=uuid4(),
                group_id=group_id,
                user_id=member_id,
                status="accepted",
            )
        )
        db.commit()

        # Create shared review with club
        self._create_review_via_api(
            client,
            author_headers,
            book_id=book_id,
            visibility="shared",
            shared_with_type="club",
            shared_with_id=club_id,
        )

        # Club member should see it
        response = client.get(f"/books/{book_id}/reviews", headers=member_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["shared_with_type"] == "club"
        assert data[0]["shared_with_id"] == str(club_id)

    def test_user_sees_own_reviews_regardless_of_visibility(self):
        """Author always sees their own reviews, regardless of visibility setting."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        book_id = uuid4()
        group_id = uuid4()

        # Create private and shared reviews (shared with a nonexistent group — doesn't matter for author)
        self._create_review_via_api(
            client, headers, book_id=book_id, visibility="private", rating=1
        )
        self._create_review_via_api(
            client,
            headers,
            book_id=book_id,
            visibility="shared",
            shared_with_type="group",
            shared_with_id=group_id,
            rating=5,
        )

        response = client.get(f"/books/{book_id}/reviews", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
