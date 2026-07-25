"""Integration tests for EditReview and DeleteReview use cases + endpoints.

Tests author-only authorization, visibility invariant enforcement during edits,
and correct deletion behavior.
Reference: reviews/design.md, ADR-0007, requirements.md Req 1.4
"""

from uuid import uuid4

import pytest

from app.reviews.application.delete_review import DeleteReview, DeleteReviewRequest
from app.reviews.application.edit_review import (
    EditReview,
    EditReviewRequest,
    ForbiddenError,
    ReviewNotFoundError,
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

    def update(self, review: Review) -> Review:
        self.reviews[review.id] = review
        return review

    def delete(self, review_id) -> None:
        self.reviews.pop(review_id, None)


# --- EditReview use case tests ---


class TestEditReviewUseCase:
    """Unit tests for EditReview use case with in-memory repository."""

    def _create_review(self, repo, user_id=None, **kwargs):
        """Helper to create and save a review."""
        defaults = {
            "user_id": user_id or uuid4(),
            "book_id": uuid4(),
            "rating": 3,
            "visibility": Visibility.PRIVATE,
        }
        defaults.update(kwargs)
        review = Review(**defaults)
        repo.save(review)
        return review

    def test_author_can_edit_rating(self):
        """Req 1.4: Author can edit their own review."""
        repo = InMemoryReviewRepository()
        author_id = uuid4()
        review = self._create_review(repo, user_id=author_id)
        uc = EditReview(review_repository=repo)

        updated = uc.execute(
            EditReviewRequest(
                review_id=review.id,
                user_id=author_id,
                rating=5,
            )
        )

        assert updated.rating == 5
        assert updated.id == review.id

    def test_author_can_edit_text(self):
        """Req 1.4: Author can update review text."""
        repo = InMemoryReviewRepository()
        author_id = uuid4()
        review = self._create_review(repo, user_id=author_id, text="Old text")
        uc = EditReview(review_repository=repo)

        updated = uc.execute(
            EditReviewRequest(
                review_id=review.id,
                user_id=author_id,
                text="New text",
            )
        )

        assert updated.text == "New text"

    def test_author_can_change_visibility_private_to_shared(self):
        """Req 1.4: Author can change visibility from private to shared."""
        repo = InMemoryReviewRepository()
        author_id = uuid4()
        group_id = uuid4()
        review = self._create_review(repo, user_id=author_id)
        uc = EditReview(review_repository=repo)

        updated = uc.execute(
            EditReviewRequest(
                review_id=review.id,
                user_id=author_id,
                visibility=Visibility.SHARED,
                shared_with_type=SharedWithType.GROUP,
                shared_with_id=group_id,
            )
        )

        assert updated.visibility == Visibility.SHARED
        assert updated.shared_with_type == SharedWithType.GROUP
        assert updated.shared_with_id == group_id

    def test_author_can_change_visibility_shared_to_private(self):
        """Req 1.4: Author can change visibility from shared to private."""
        repo = InMemoryReviewRepository()
        author_id = uuid4()
        group_id = uuid4()
        review = self._create_review(
            repo,
            user_id=author_id,
            visibility=Visibility.SHARED,
            shared_with_type=SharedWithType.GROUP,
            shared_with_id=group_id,
        )
        uc = EditReview(review_repository=repo)

        updated = uc.execute(
            EditReviewRequest(
                review_id=review.id,
                user_id=author_id,
                visibility=Visibility.PRIVATE,
            )
        )

        assert updated.visibility == Visibility.PRIVATE
        assert updated.shared_with_type is None
        assert updated.shared_with_id is None

    def test_non_author_cannot_edit(self):
        """Req 1.4: Non-author receives ForbiddenError."""
        repo = InMemoryReviewRepository()
        author_id = uuid4()
        other_user_id = uuid4()
        review = self._create_review(repo, user_id=author_id)
        uc = EditReview(review_repository=repo)

        with pytest.raises(ForbiddenError):
            uc.execute(
                EditReviewRequest(
                    review_id=review.id,
                    user_id=other_user_id,
                    rating=1,
                )
            )

    def test_edit_nonexistent_review_raises_not_found(self):
        """404 case: Review does not exist."""
        repo = InMemoryReviewRepository()
        uc = EditReview(review_repository=repo)

        with pytest.raises(ReviewNotFoundError):
            uc.execute(
                EditReviewRequest(
                    review_id=uuid4(),
                    user_id=uuid4(),
                    rating=5,
                )
            )

    def test_edit_shared_without_target_raises_value_error(self):
        """Property 2: Changing to shared without target violates invariants."""
        repo = InMemoryReviewRepository()
        author_id = uuid4()
        review = self._create_review(repo, user_id=author_id)
        uc = EditReview(review_repository=repo)

        with pytest.raises(ValueError):
            uc.execute(
                EditReviewRequest(
                    review_id=review.id,
                    user_id=author_id,
                    visibility=Visibility.SHARED,
                )
            )


# --- DeleteReview use case tests ---


class TestDeleteReviewUseCase:
    """Unit tests for DeleteReview use case with in-memory repository."""

    def _create_review(self, repo, user_id=None, **kwargs):
        """Helper to create and save a review."""
        defaults = {
            "user_id": user_id or uuid4(),
            "book_id": uuid4(),
            "rating": 3,
            "visibility": Visibility.PRIVATE,
        }
        defaults.update(kwargs)
        review = Review(**defaults)
        repo.save(review)
        return review

    def test_author_can_delete(self):
        """Req 1.4: Author can delete their own review."""
        repo = InMemoryReviewRepository()
        author_id = uuid4()
        review = self._create_review(repo, user_id=author_id)
        uc = DeleteReview(review_repository=repo)

        uc.execute(DeleteReviewRequest(review_id=review.id, user_id=author_id))

        assert repo.find_by_id(review.id) is None

    def test_non_author_cannot_delete(self):
        """Req 1.4: Non-author receives ForbiddenError."""
        repo = InMemoryReviewRepository()
        author_id = uuid4()
        other_user_id = uuid4()
        review = self._create_review(repo, user_id=author_id)
        uc = DeleteReview(review_repository=repo)

        with pytest.raises(ForbiddenError):
            uc.execute(
                DeleteReviewRequest(review_id=review.id, user_id=other_user_id)
            )

        # Review should still exist
        assert repo.find_by_id(review.id) is not None

    def test_delete_nonexistent_review_raises_not_found(self):
        """404 case: Review does not exist."""
        repo = InMemoryReviewRepository()
        uc = DeleteReview(review_repository=repo)

        with pytest.raises(ReviewNotFoundError):
            uc.execute(DeleteReviewRequest(review_id=uuid4(), user_id=uuid4()))


# --- Endpoint tests ---


class TestEditReviewEndpoint:
    """Integration tests for PATCH /reviews/{id} via TestClient."""

    def _get_auth_header(self, user_id=None):
        """Create a valid auth token for testing."""
        from app.auth.jwt import create_access_token

        uid = user_id or uuid4()
        token = create_access_token(str(uid))
        return {"Authorization": f"Bearer {token}"}, uid

    def _create_review_via_api(self, client, headers, **kwargs):
        """Helper to create a review via the API."""
        body = {
            "book_id": str(uuid4()),
            "rating": 3,
            "visibility": "private",
        }
        body.update(kwargs)
        response = client.post("/reviews/", json=body, headers=headers)
        assert response.status_code == 201
        return response.json()

    def test_edit_rating_returns_200(self):
        """Req 1.4: Author can edit rating via PATCH."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        review = self._create_review_via_api(client, headers)

        response = client.patch(
            f"/reviews/{review['id']}",
            json={"rating": 5},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        assert data["id"] == review["id"]

    def test_edit_text_returns_200(self):
        """Req 1.4: Author can edit text via PATCH."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        review = self._create_review_via_api(client, headers, text="Original")

        response = client.patch(
            f"/reviews/{review['id']}",
            json={"text": "Updated text"},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["text"] == "Updated text"

    def test_edit_by_non_author_returns_403(self):
        """Req 1.4: Non-author gets 403 Forbidden."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        author_headers, author_id = self._get_auth_header()
        other_headers, other_id = self._get_auth_header()
        review = self._create_review_via_api(client, author_headers)

        response = client.patch(
            f"/reviews/{review['id']}",
            json={"rating": 1},
            headers=other_headers,
        )

        assert response.status_code == 403

    def test_edit_nonexistent_review_returns_404(self):
        """404 when review does not exist."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, _ = self._get_auth_header()

        response = client.patch(
            f"/reviews/{uuid4()}",
            json={"rating": 5},
            headers=headers,
        )

        assert response.status_code == 404

    def test_edit_visibility_to_shared_with_target(self):
        """Req 1.4 + Property 2: Changing to shared requires target."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        review = self._create_review_via_api(client, headers)
        group_id = str(uuid4())

        response = client.patch(
            f"/reviews/{review['id']}",
            json={
                "visibility": "shared",
                "shared_with_type": "group",
                "shared_with_id": group_id,
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["visibility"] == "shared"
        assert data["shared_with_type"] == "group"
        assert data["shared_with_id"] == group_id

    def test_edit_visibility_to_shared_without_target_returns_422(self):
        """Error case: changing to shared without target → 422."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        review = self._create_review_via_api(client, headers)

        response = client.patch(
            f"/reviews/{review['id']}",
            json={"visibility": "shared"},
            headers=headers,
        )

        assert response.status_code == 422


class TestDeleteReviewEndpoint:
    """Integration tests for DELETE /reviews/{id} via TestClient."""

    def _get_auth_header(self, user_id=None):
        """Create a valid auth token for testing."""
        from app.auth.jwt import create_access_token

        uid = user_id or uuid4()
        token = create_access_token(str(uid))
        return {"Authorization": f"Bearer {token}"}, uid

    def _create_review_via_api(self, client, headers, **kwargs):
        """Helper to create a review via the API."""
        body = {
            "book_id": str(uuid4()),
            "rating": 3,
            "visibility": "private",
        }
        body.update(kwargs)
        response = client.post("/reviews/", json=body, headers=headers)
        assert response.status_code == 201
        return response.json()

    def test_delete_by_author_returns_204(self):
        """Req 1.4: Author can delete their review."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        review = self._create_review_via_api(client, headers)

        response = client.delete(
            f"/reviews/{review['id']}",
            headers=headers,
        )

        assert response.status_code == 204

    def test_delete_by_non_author_returns_403(self):
        """Req 1.4: Non-author gets 403 Forbidden."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        author_headers, author_id = self._get_auth_header()
        other_headers, other_id = self._get_auth_header()
        review = self._create_review_via_api(client, author_headers)

        response = client.delete(
            f"/reviews/{review['id']}",
            headers=other_headers,
        )

        assert response.status_code == 403

    def test_delete_nonexistent_review_returns_404(self):
        """404 when review does not exist."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, _ = self._get_auth_header()

        response = client.delete(
            f"/reviews/{uuid4()}",
            headers=headers,
        )

        assert response.status_code == 404

    def test_deleted_review_is_not_retrievable_via_edit(self):
        """After deletion, editing the same review returns 404."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        headers, user_id = self._get_auth_header()
        review = self._create_review_via_api(client, headers)

        # Delete
        delete_resp = client.delete(f"/reviews/{review['id']}", headers=headers)
        assert delete_resp.status_code == 204

        # Try to edit — should get 404
        edit_resp = client.patch(
            f"/reviews/{review['id']}",
            json={"rating": 5},
            headers=headers,
        )
        assert edit_resp.status_code == 404
