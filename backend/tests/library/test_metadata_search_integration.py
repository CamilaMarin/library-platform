"""Integration tests for GET /books/metadata/search endpoint.

Tests cover:
- ISBN search happy path (mocked adapter)
- Malformed ISBN → 422
- Text search happy path
- Missing auth → 401
- Provider unavailable → 503
- Empty text query → 200 with empty array
- ISBN not found → 200 with empty array

Reference: .kiro/specs/metadata-import/requirements.md Req 7.1, 7.2, 7.3, 7.4, 4.1, 1.3
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.library.application.protocols import MetadataProviderError
from app.library.domain.entities import BookMetadata
from app.main import app

client = TestClient(app)


def _auth_headers(user_id=None):
    """Generate auth headers with a valid access token."""
    uid = user_id or uuid4()
    token = create_access_token(str(uid))
    return {"Authorization": f"Bearer {token}"}


class TestMetadataSearchISBN:
    """Integration tests for ISBN-based metadata search."""

    @patch("app.library.interface.books_router.OpenLibraryAdapter")
    def test_isbn_search_happy_path(self, mock_adapter_cls):
        """Req 7.1: ISBN search returns 200 with single result from provider."""
        mock_adapter = MagicMock()
        mock_adapter_cls.return_value = mock_adapter
        mock_adapter.search_by_isbn.return_value = BookMetadata(
            title="Don Quixote",
            author="Miguel de Cervantes",
            isbn="9780142437230",
            genres=["Fiction", "Classic"],
            description="A classic Spanish novel.",
            pages=982,
        )

        response = client.get(
            "/books/metadata/search?query=9780142437230&type=isbn",
            headers=_auth_headers(),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Don Quixote"
        assert data[0]["author"] == "Miguel de Cervantes"
        assert data[0]["isbn"] == "9780142437230"
        assert data[0]["genres"] == ["Fiction", "Classic"]
        assert data[0]["description"] == "A classic Spanish novel."
        assert data[0]["pages"] == 982

    @patch("app.library.interface.books_router.OpenLibraryAdapter")
    def test_isbn_not_found_returns_empty_array(self, mock_adapter_cls):
        """Req 7.2: ISBN not found in provider returns 200 with empty array."""
        mock_adapter = MagicMock()
        mock_adapter_cls.return_value = mock_adapter
        mock_adapter.search_by_isbn.return_value = None

        response = client.get(
            "/books/metadata/search?query=9780000000000&type=isbn",
            headers=_auth_headers(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_malformed_isbn_returns_422(self):
        """Req 1.3: Malformed ISBN (not 10 or 13 digits) returns 422."""
        response = client.get(
            "/books/metadata/search?query=abc&type=isbn",
            headers=_auth_headers(),
        )

        assert response.status_code == 422
        data = response.json()
        assert data["detail"] == "invalid_isbn_format"

    def test_short_isbn_returns_422(self):
        """Req 1.3: ISBN with wrong digit count returns 422."""
        response = client.get(
            "/books/metadata/search?query=12345&type=isbn",
            headers=_auth_headers(),
        )

        assert response.status_code == 422
        data = response.json()
        assert data["detail"] == "invalid_isbn_format"


class TestMetadataSearchText:
    """Integration tests for text-based metadata search."""

    @patch("app.library.interface.books_router.OpenLibraryAdapter")
    def test_text_search_happy_path(self, mock_adapter_cls):
        """Req 7.3: Text search returns 200 with results array."""
        mock_adapter = MagicMock()
        mock_adapter_cls.return_value = mock_adapter
        mock_adapter.search_by_text.return_value = [
            BookMetadata(
                title="One Hundred Years of Solitude",
                author="Gabriel Garcia Marquez",
                isbn="9780060883287",
                genres=["Fiction"],
                pages=417,
            ),
            BookMetadata(
                title="Love in the Time of Cholera",
                author="Gabriel Garcia Marquez",
                isbn="9780307389732",
                genres=["Fiction", "Romance"],
                pages=348,
            ),
        ]

        response = client.get(
            "/books/metadata/search?query=Garcia+Marquez&type=text",
            headers=_auth_headers(),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "One Hundred Years of Solitude"
        assert data[0]["author"] == "Gabriel Garcia Marquez"
        assert data[1]["title"] == "Love in the Time of Cholera"

    @patch("app.library.interface.books_router.OpenLibraryAdapter")
    def test_empty_text_query_returns_empty_array(self, mock_adapter_cls):
        """Req 7.4: Empty text query returns 200 with empty array."""
        response = client.get(
            "/books/metadata/search?query=+&type=text",
            headers=_auth_headers(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []
        # Adapter should not be called for empty query
        mock_adapter_cls.return_value.search_by_text.assert_not_called()

    @patch("app.library.interface.books_router.OpenLibraryAdapter")
    def test_whitespace_only_text_query_returns_empty_array(self, mock_adapter_cls):
        """Req 7.4: Whitespace-only text query returns 200 with empty array."""
        response = client.get(
            "/books/metadata/search?query=   &type=text",
            headers=_auth_headers(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestMetadataSearchAuth:
    """Integration tests for authentication requirements."""

    def test_missing_auth_header_rejected(self):
        """Req 7.1: Missing Authorization header is rejected (422 - required header)."""
        response = client.get(
            "/books/metadata/search?query=9780142437230&type=isbn",
        )

        # FastAPI returns 422 for missing required Header(...) parameters
        assert response.status_code == 422

    def test_invalid_token_returns_401(self):
        """Req 7.1: Invalid/expired token returns 401."""
        response = client.get(
            "/books/metadata/search?query=9780142437230&type=isbn",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401


class TestMetadataSearchErrors:
    """Integration tests for error scenarios."""

    @patch("app.library.interface.books_router.OpenLibraryAdapter")
    def test_provider_unavailable_returns_503(self, mock_adapter_cls):
        """Req 4.1: Provider error returns 503 with structured error detail."""
        mock_adapter = MagicMock()
        mock_adapter_cls.return_value = mock_adapter
        mock_adapter.search_by_isbn.side_effect = MetadataProviderError(
            "Connection timeout"
        )

        response = client.get(
            "/books/metadata/search?query=9780142437230&type=isbn",
            headers=_auth_headers(),
        )

        assert response.status_code == 503
        data = response.json()
        assert data["detail"] == "external_metadata_service_unavailable"

    @patch("app.library.interface.books_router.OpenLibraryAdapter")
    def test_provider_error_on_text_search_returns_503(self, mock_adapter_cls):
        """Req 4.1: Provider error during text search also returns 503."""
        mock_adapter = MagicMock()
        mock_adapter_cls.return_value = mock_adapter
        mock_adapter.search_by_text.side_effect = MetadataProviderError(
            "DNS resolution failed"
        )

        response = client.get(
            "/books/metadata/search?query=Cervantes&type=text",
            headers=_auth_headers(),
        )

        assert response.status_code == 503
        data = response.json()
        assert data["detail"] == "external_metadata_service_unavailable"
