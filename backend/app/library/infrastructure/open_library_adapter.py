"""OpenLibraryAdapter — MetadataProvider implementation using Open Library API.

Endpoints used:
- ISBN lookup: https://openlibrary.org/isbn/{isbn}.json
- Text search: https://openlibrary.org/search.json?q={query}&limit={limit}&fields=...
- Author resolution: https://openlibrary.org/authors/{key}.json

Privacy (Req 6.1): Only the query string (ISBN or title/author text) is transmitted.
No user identifiers, tokens, or personal data are sent to the external API.

Reference: ADR-0017 (cloud agnostic — infrastructure implements application protocols)
"""

import logging

import httpx

from app.library.application.protocols import MetadataProviderError
from app.library.domain.entities import BookMetadata

logger = logging.getLogger(__name__)


class OpenLibraryAdapter:
    """MetadataProvider implementation using the Open Library API.

    Satisfies the MetadataProvider protocol defined in
    app.library.application.protocols.

    Reference: ADR-0017 (cloud agnostic — infrastructure implements application protocols)
    """

    BASE_URL = "https://openlibrary.org"
    TIMEOUT_SECONDS = 5.0
    SEARCH_FIELDS = "title,author_name,isbn,number_of_pages_median,subject"
    USER_AGENT = "EntreLineas/1.0 (library-platform)"

    def __init__(self, timeout: float | None = None):
        self._timeout = timeout if timeout is not None else self.TIMEOUT_SECONDS
        self._headers = {"User-Agent": self.USER_AGENT}

    def search_by_isbn(self, isbn: str) -> BookMetadata | None:
        """Fetch a single edition by ISBN from Open Library.

        Args:
            isbn: A normalized ISBN-10 or ISBN-13 (digits only, no hyphens).

        Returns:
            BookMetadata if found, None if no match or ISBN not found (404).

        Raises:
            MetadataProviderError: On network failure, timeout, or unexpected HTTP error.
        """
        url = f"{self.BASE_URL}/isbn/{isbn}.json"

        try:
            response = httpx.get(
                url, headers=self._headers, timeout=self._timeout, follow_redirects=True
            )
        except httpx.TimeoutException as exc:
            raise MetadataProviderError(
                f"Timeout fetching ISBN {isbn} from Open Library"
            ) from exc
        except httpx.ConnectError as exc:
            raise MetadataProviderError(
                "Unable to connect to Open Library"
            ) from exc
        except httpx.HTTPError as exc:
            raise MetadataProviderError(
                f"HTTP error contacting Open Library: {exc}"
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            raise MetadataProviderError(
                f"Open Library returned status {response.status_code} for ISBN {isbn}"
            )

        try:
            data = response.json()
        except (ValueError, KeyError):
            logger.warning("Invalid JSON response from Open Library for ISBN %s", isbn)
            return None

        return self._map_isbn_response(data, isbn)

    def search_by_text(self, query: str, limit: int = 10) -> list[BookMetadata]:
        """Search Open Library by free text (title/author).

        Args:
            query: Free-text search string (title, author, or combination).
            limit: Maximum results to return (default 10, max 10).

        Returns:
            List of BookMetadata results, possibly empty.

        Raises:
            MetadataProviderError: On network failure, timeout, or unexpected HTTP error.
        """
        url = f"{self.BASE_URL}/search.json"
        params = {
            "q": query,
            "limit": min(limit, 10),
            "fields": self.SEARCH_FIELDS,
        }

        try:
            response = httpx.get(
                url, params=params, headers=self._headers, timeout=self._timeout
            )
        except httpx.TimeoutException as exc:
            raise MetadataProviderError(
                "Timeout searching Open Library"
            ) from exc
        except httpx.ConnectError as exc:
            raise MetadataProviderError(
                "Unable to connect to Open Library"
            ) from exc
        except httpx.HTTPError as exc:
            raise MetadataProviderError(
                f"HTTP error contacting Open Library: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise MetadataProviderError(
                f"Open Library returned status {response.status_code} for text search"
            )

        try:
            data = response.json()
        except (ValueError, KeyError):
            logger.warning("Invalid JSON response from Open Library text search")
            return []

        docs = data.get("docs", [])
        results: list[BookMetadata] = []

        for doc in docs:
            mapped = self._map_search_result(doc)
            if mapped is not None:
                results.append(mapped)

        return results

    def _map_isbn_response(self, data: dict, isbn: str) -> BookMetadata | None:
        """Map an Open Library ISBN endpoint response to BookMetadata.

        Returns None if the response lacks a title (minimum required field).
        """
        title = data.get("title")
        if not title:
            logger.warning("Open Library ISBN response missing title for %s", isbn)
            return None

        # Resolve author name from author key (secondary request)
        author = self._resolve_author(data)

        # Extract genres from subjects (first 5)
        subjects = data.get("subjects", [])
        genres = subjects[:5] if isinstance(subjects, list) else []

        # Extract description — may be a string or a dict
        description = self._extract_description(data)

        # Pages
        pages = data.get("number_of_pages")
        if pages is not None:
            try:
                pages = int(pages)
            except (ValueError, TypeError):
                pages = None

        # ISBN — prefer isbn_13, fallback to isbn_10, then input isbn
        result_isbn = self._extract_isbn(data, isbn)

        return BookMetadata(
            title=title,
            author=author,
            genres=genres,
            description=description,
            pages=pages,
            isbn=result_isbn,
        )

    def _map_search_result(self, doc: dict) -> BookMetadata | None:
        """Map a single Open Library search result document to BookMetadata.

        Returns None if the document lacks a title.
        """
        title = doc.get("title")
        if not title:
            return None

        # Author is available directly in search results
        author_names = doc.get("author_name", [])
        author = author_names[0] if author_names else None

        # Genres from subject (first 5)
        subjects = doc.get("subject", [])
        genres = subjects[:5] if isinstance(subjects, list) else []

        # Pages from median
        pages = doc.get("number_of_pages_median")
        if pages is not None:
            try:
                pages = int(pages)
            except (ValueError, TypeError):
                pages = None

        # ISBN — first from list
        isbn_list = doc.get("isbn", [])
        isbn = isbn_list[0] if isbn_list else None

        return BookMetadata(
            title=title,
            author=author,
            genres=genres,
            description=None,  # Not available in search results
            pages=pages,
            isbn=isbn,
        )

    def _resolve_author(self, data: dict) -> str | None:
        """Resolve author name from the authors key list.

        The ISBN endpoint returns authors as key references like:
        {"authors": [{"key": "/authors/OL123A"}]}

        This method fetches the first author's name via a secondary request.
        Falls back to None on any failure.
        """
        authors = data.get("authors", [])
        if not authors or not isinstance(authors, list):
            return None

        first_author = authors[0]
        if isinstance(first_author, dict):
            author_key = first_author.get("key")
        else:
            return None

        if not author_key:
            return None

        url = f"{self.BASE_URL}{author_key}.json"

        try:
            response = httpx.get(
                url, headers=self._headers, timeout=self._timeout, follow_redirects=True
            )
            if response.status_code != 200:
                logger.warning(
                    "Failed to resolve author %s: status %d",
                    author_key,
                    response.status_code,
                )
                return None

            author_data = response.json()
            return author_data.get("name")

        except httpx.TimeoutException:
            logger.warning("Timeout resolving author %s", author_key)
            return None
        except httpx.HTTPError:
            logger.warning("HTTP error resolving author %s", author_key)
            return None
        except (ValueError, KeyError):
            logger.warning("Invalid JSON resolving author %s", author_key)
            return None

    def _extract_description(self, data: dict) -> str | None:
        """Extract description from Open Library response.

        The description field can be:
        - A plain string
        - A dict like {"type": "/type/text", "value": "..."}
        - Missing entirely (fall back to 'notes')
        """
        description = data.get("description")

        if description is None:
            # Fallback to notes
            description = data.get("notes")

        if description is None:
            return None

        if isinstance(description, dict):
            return description.get("value")

        if isinstance(description, str):
            return description

        return None

    def _extract_isbn(self, data: dict, fallback_isbn: str) -> str:
        """Extract the best ISBN from the response, preferring ISBN-13.

        Falls back to the input ISBN if neither isbn_13 nor isbn_10 is found.
        """
        isbn_13 = data.get("isbn_13", [])
        if isbn_13 and isinstance(isbn_13, list):
            return isbn_13[0]

        isbn_10 = data.get("isbn_10", [])
        if isbn_10 and isinstance(isbn_10, list):
            return isbn_10[0]

        return fallback_isbn
