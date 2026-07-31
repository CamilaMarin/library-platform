"""SearchBookMetadata use case.

Searches external metadata sources by ISBN or free text to autocomplete
book fields during creation. Results are transient suggestions — never persisted.

Reference: .kiro/specs/metadata-import/requirements.md Req 1.1, 1.2, 1.3, 2.1, 2.2, 4.1
"""

from dataclasses import dataclass

from app.library.application.protocols import MetadataProvider
from app.library.domain.entities import BookMetadata


@dataclass
class SearchBookMetadataRequest:
    """Input for SearchBookMetadata use case."""

    query: str
    search_type: str = "text"  # "isbn" or "text"


class InvalidIsbnError(ValueError):
    """Raised when the ISBN string is not 10 or 13 digits after normalization."""

    def __init__(self, isbn: str):
        super().__init__(f"Invalid ISBN format: '{isbn}'. Must be 10 or 13 digits.")
        self.isbn = isbn


class SearchBookMetadata:
    """Use case: search external sources for book metadata.

    Two modes:
    - isbn: normalizes input, validates format, queries provider for a single match.
    - text: strips whitespace, delegates to provider for up to 10 results.

    Does NOT catch MetadataProviderError — it propagates to the interface layer
    for proper HTTP error mapping (Req 4.1).
    """

    def __init__(self, metadata_provider: MetadataProvider):
        self._provider = metadata_provider

    def execute(self, request: SearchBookMetadataRequest) -> list[BookMetadata]:
        """Execute the metadata search."""
        if request.search_type == "isbn":
            normalized = self._normalize_isbn(request.query)
            self._validate_isbn(normalized)
            result = self._provider.search_by_isbn(normalized)
            return [result] if result else []
        else:
            query = request.query.strip()
            if not query:
                return []
            return self._provider.search_by_text(query, limit=10)

    @staticmethod
    def _normalize_isbn(raw: str) -> str:
        """Strip hyphens and spaces from an ISBN string."""
        return raw.replace("-", "").replace(" ", "").strip()

    @staticmethod
    def _validate_isbn(isbn: str) -> None:
        """Raise InvalidIsbnError if isbn is not exactly 10 or 13 digits."""
        if not isbn.isdigit() or len(isbn) not in (10, 13):
            raise InvalidIsbnError(isbn)
