"""Integration tests for CreateReview use case + POST /reviews endpoint.

Tests visibility invariants, explicit visibility enforcement, and error cases.
Reference: reviews/design.md Properties 1-2, ADR-0007, requirements.md Req 1.1, 1.2, 1.3, 1.5
"""

from uuid import uuid4

import pytest

from app.reviews.application.create_review import (
    CreateReview,
    CreateReviewRequest,
    InvalidVisibilityTargetError,
)
from app.reviews.domain.entities import Review, SharedWithType, Visibility

# --- In-memory test double ---


class InMemoryReviewRepository:
    def __init__(self):
        self.reviews: dict = {}

    def save(self, review: Review) -> Review:
        self.reviews[review.id] = review
        return review

    def find_by_id(self, review_id):
        return self.reviews.get(review_id)


# --- Use case tests ---


class TestCreateReviewUseCase:
    """Unit tests for CreateReview use case with in-memory repository."""

    def test_creates_private_review_successfully(self):
        """Req 1.1, 1.2: Create review with rating and private visibility."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)

        review = uc.execute(
            CreateReviewRequest(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=4,
                visibility=Visibility.PRIVATE,
                text="Great book!",
            )
        )

        assert review.rating == 4
        assert review.text == "Great book!"
        assert review.visibility == Visibility.PRIVATE
        assert review.shared_with_type is None
        assert review.shared_with_id is None
        assert repo.find_by_id(review.id) is not None

    def test_creates_shared_review_with_group(self):
        """Req 1.3: Shared review requires explicit target group."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)
        group_id = uuid4()

        review = uc.execute(
            CreateReviewRequest(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=5,
                visibility=Visibility.SHARED,
                shared_with_type=SharedWithType.GROUP,
                shared_with_id=group_id,
            )
        )

        assert review.visibility == Visibility.SHARED
        assert review.shared_with_type == SharedWithType.GROUP
        assert review.shared_with_id == group_id

    def test_creates_shared_review_with_club(self):
        """Req 1.3: Shared review requires explicit target club."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)
        club_id = uuid4()

        review = uc.execute(
            CreateReviewRequest(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=3,
                visibility=Visibility.SHARED,
                text="Interesting read.",
                shared_with_type=SharedWithType.CLUB,
                shared_with_id=club_id,
            )
        )

        assert review.visibility == Visibility.SHARED
        assert review.shared_with_type == SharedWithType.CLUB
        assert review.shared_with_id == club_id

    def test_creates_review_without_text(self):
        """Req 1.1: Text is optional."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)

        review = uc.execute(
            CreateReviewRequest(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=2,
                visibility=Visibility.PRIVATE,
            )
        )

        assert review.text is None
        assert review.rating == 2

    def test_rejects_shared_without_type(self):
        """Req 1.3: Shared visibility without shared_with_type raises error."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)

        with pytest.raises(InvalidVisibilityTargetError):
            uc.execute(
                CreateReviewRequest(
                    user_id=uuid4(),
                    book_id=uuid4(),
                    rating=4,
                    visibility=Visibility.SHARED,
                    shared_with_id=uuid4(),
                )
            )

    def test_rejects_shared_without_id(self):
        """Req 1.3: Shared visibility without shared_with_id raises error."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)

        with pytest.raises(InvalidVisibilityTargetError):
            uc.execute(
                CreateReviewRequest(
                    user_id=uuid4(),
                    book_id=uuid4(),
                    rating=4,
                    visibility=Visibility.SHARED,
                    shared_with_type=SharedWithType.GROUP,
                )
            )

    def test_rejects_shared_without_both(self):
        """Req 1.3: Shared visibility without any target raises error."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)

        with pytest.raises(InvalidVisibilityTargetError):
            uc.execute(
                CreateReviewRequest(
                    user_id=uuid4(),
                    book_id=uuid4(),
                    rating=4,
                    visibility=Visibility.SHARED,
                )
            )

    def test_rejects_invalid_rating_too_low(self):
        """Req 1.1: Rating must be 1-5."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)

        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            uc.execute(
                CreateReviewRequest(
                    user_id=uuid4(),
                    book_id=uuid4(),
                    rating=0,
                    visibility=Visibility.PRIVATE,
                )
            )

    def test_rejects_invalid_rating_too_high(self):
        """Req 1.1: Rating must be 1-5."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)

        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            uc.execute(
                CreateReviewRequest(
                    user_id=uuid4(),
                    book_id=uuid4(),
                    rating=6,
                    visibility=Visibility.PRIVATE,
                )
            )

    def test_property_1_private_implies_null_shared_with(self):
        """Property 1: visibility == 'private' implies shared_with is NULL."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)

        review = uc.execute(
            CreateReviewRequest(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=3,
                visibility=Visibility.PRIVATE,
            )
        )

        assert review.shared_with_type is None
        assert review.shared_with_id is None

    def test_property_2_shared_implies_non_null_shared_with(self):
        """Property 2: visibility == 'shared' implies shared_with is NOT NULL."""
        repo = InMemoryReviewRepository()
        uc = CreateReview(review_repository=repo)
        target_id = uuid4()

        review = uc.execute(
            CreateReviewRequest(
                user_id=uuid4(),
                book_id=uuid4(),
                rating=5,
                visibility=Visibility.SHARED,
                shared_with_type=SharedWithType.GROUP,
                shared_with_id=target_id,
            )
        )

        assert review.shared_with_type is not None
        assert review.shared_with_id is not None


# --- Endpoint tests ---


class TestCreateReviewEndpoint:
    """Integration tests for POST /reviews via TestClient."""

    def _get_auth_header(self):
        """Create a valid auth token for testing."""
        from app.auth.jwt import create_access_token

        user_id = uuid4()
        token = create_access_token(str(user_id))
        return {"Authorization": f"Bearer {token}"}, user_id

    def test_create_private_review_returns_201(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()

        response = client.post(
            "/reviews/",
            json={
                "book_id": str(uuid4()),
                "rating": 4,
                "visibility": "private",
                "text": "Loved it!",
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 4
        assert data["visibility"] == "private"
        assert data["text"] == "Loved it!"
        assert data["shared_with_type"] is None
        assert data["shared_with_id"] is None

    def test_create_shared_review_with_group_returns_201(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        group_id = str(uuid4())

        response = client.post(
            "/reviews/",
            json={
                "book_id": str(uuid4()),
                "rating": 5,
                "visibility": "shared",
                "shared_with_type": "group",
                "shared_with_id": group_id,
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["visibility"] == "shared"
        assert data["shared_with_type"] == "group"
        assert data["shared_with_id"] == group_id

    def test_create_shared_review_without_target_returns_422(self):
        """Error case: shared visibility without shared_with -> 422 invalid_visibility_target."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, _ = self._get_auth_header()

        response = client.post(
            "/reviews/",
            json={
                "book_id": str(uuid4()),
                "rating": 3,
                "visibility": "shared",
            },
            headers=headers,
        )

        assert response.status_code == 422

    def test_missing_visibility_returns_422(self):
        """Req 1.5: visibility is required, never defaults."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, _ = self._get_auth_header()

        response = client.post(
            "/reviews/",
            json={
                "book_id": str(uuid4()),
                "rating": 4,
                "text": "No visibility specified",
            },
            headers=headers,
        )

        assert response.status_code == 422

    def test_invalid_rating_returns_422(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, _ = self._get_auth_header()

        response = client.post(
            "/reviews/",
            json={
                "book_id": str(uuid4()),
                "rating": 0,
                "visibility": "private",
            },
            headers=headers,
        )

        assert response.status_code == 422

    def test_unauthenticated_request_returns_401(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)

        response = client.post(
            "/reviews/",
            json={
                "book_id": str(uuid4()),
                "rating": 4,
                "visibility": "private",
            },
        )

        assert response.status_code in (401, 422)

    def test_private_review_with_shared_with_returns_422(self):
        """Property 1: private visibility must not have shared_with fields."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, _ = self._get_auth_header()

        response = client.post(
            "/reviews/",
            json={
                "book_id": str(uuid4()),
                "rating": 4,
                "visibility": "private",
                "shared_with_type": "group",
                "shared_with_id": str(uuid4()),
            },
            headers=headers,
        )

        assert response.status_code == 422
