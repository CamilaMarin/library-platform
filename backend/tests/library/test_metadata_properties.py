"""Property-based tests for the Metadata Import feature.

Uses Hypothesis to validate correctness properties defined in
.kiro/specs/metadata-import/design.md

Reference: design.md — Correctness Properties section
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.library.application.protocols import MetadataProviderError
from app.library.application.search_book_metadata import (
    InvalidIsbnError,
    SearchBookMetadata,
    SearchBookMetadataRequest,
)
from app.library.domain.entities import BookMetadata

# --- Strategies ---


def isbn_digits_strategy(length: int) -> st.SearchStrategy[str]:
    """Generate a string of exactly `length` digit characters with random hyphens/spaces."""
    digits = st.text(alphabet="0123456789", min_size=length, max_size=length)

    def intersperse_separators(digit_str: str) -> st.SearchStrategy[str]:
        """Insert arbitrary hyphens and spaces between digits."""
        # For each position between/around digits, optionally insert separators
        separators = st.text(alphabet="- ", min_size=0, max_size=3)

        @st.composite
        def build(draw: st.DrawFn) -> str:
            result = []
            for char in digit_str:
                result.append(draw(separators))
                result.append(char)
            result.append(draw(separators))
            return "".join(result)

        return build()

    return digits.flatmap(intersperse_separators)


@st.composite
def valid_isbn_strings(draw: st.DrawFn) -> str:
    """Generate strings with exactly 10 or 13 digits interspersed with hyphens/spaces.

    After removing hyphens and spaces, the result is exactly 10 or 13 digit characters.
    """
    length = draw(st.sampled_from([10, 13]))
    return draw(isbn_digits_strategy(length))


@st.composite
def malformed_isbn_strings(draw: st.DrawFn) -> str:
    """Generate strings where, after removing hyphens/spaces, the result is NOT 10 or 13 digits.

    This covers:
    - Wrong digit count (not 10 or 13)
    - Non-digit characters remaining after stripping hyphens/spaces
    """
    strategy_choice = draw(st.sampled_from(["wrong_length", "non_digits"]))

    if strategy_choice == "wrong_length":
        # Generate digit strings of length != 10 and != 13
        length = draw(st.integers(min_value=0, max_value=20).filter(lambda n: n not in (10, 13)))
        digits = draw(st.text(alphabet="0123456789", min_size=length, max_size=length))
        # Optionally add some hyphens/spaces
        sep = draw(st.text(alphabet="- ", min_size=0, max_size=3))
        return sep + digits + sep
    else:
        # Generate strings that contain non-digit, non-hyphen, non-space characters
        # After removing hyphens/spaces, there will be non-digit chars
        base = draw(st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
            min_size=1,
            max_size=15,
        ).filter(lambda s: not s.replace("-", "").replace(" ", "").isdigit()
                 or len(s.replace("-", "").replace(" ", "")) not in (10, 13)))
        # Ensure it has at least one non-digit after stripping
        non_digit = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=3))
        return base + non_digit


@st.composite
def book_metadata_strategy(draw: st.DrawFn) -> BookMetadata:
    """Generate valid BookMetadata objects with a non-empty title."""
    title = draw(st.text(min_size=1, max_size=100).filter(lambda s: s.strip()))
    author = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    genres = draw(st.lists(st.text(min_size=1, max_size=30), max_size=5))
    description = draw(st.one_of(st.none(), st.text(min_size=1, max_size=200)))
    pages = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=5000)))
    isbn = draw(st.one_of(st.none(), st.text(alphabet="0123456789", min_size=10, max_size=13)))
    return BookMetadata(
        title=title,
        author=author,
        genres=genres,
        description=description,
        pages=pages,
        isbn=isbn,
    )


# --- Mock Provider ---


class MockMetadataProvider:
    """A configurable mock MetadataProvider for property tests."""

    def __init__(
        self,
        isbn_result: BookMetadata | None = None,
        text_results: list[BookMetadata] | None = None,
        error: MetadataProviderError | None = None,
    ):
        self._isbn_result = isbn_result
        self._text_results = text_results or []
        self._error = error

    def search_by_isbn(self, isbn: str) -> BookMetadata | None:
        if self._error:
            raise self._error
        return self._isbn_result

    def search_by_text(self, query: str, limit: int = 10) -> list[BookMetadata]:
        if self._error:
            raise self._error
        return self._text_results[:limit]


# --- Property Tests ---


@pytest.mark.property
class TestMetadataProperties:
    """Property-based tests for Metadata Import correctness properties."""

    @given(isbn_string=valid_isbn_strings())
    @settings(max_examples=100)
    def test_isbn_normalization_accepts_valid_formats(self, isbn_string: str) -> None:
        """Property 1: ISBN normalization accepts valid formats.

        For any string composed of exactly 10 or 13 digit characters interspersed
        with arbitrary hyphens and spaces, normalizing and validating that string
        SHALL succeed without raising an error.

        **Validates: Requirements 1.1, 1.3**
        """
        normalized = SearchBookMetadata._normalize_isbn(isbn_string)
        # Should not raise — valid ISBN format
        SearchBookMetadata._validate_isbn(normalized)

    @given(isbn_string=malformed_isbn_strings())
    @settings(max_examples=100)
    def test_malformed_isbn_rejection(self, isbn_string: str) -> None:
        """Property 2: Malformed ISBN rejection.

        For any string where, after removing all hyphens and spaces, the remaining
        characters are not exclusively digits OR the digit count is neither 10 nor 13,
        the SearchBookMetadata use case with search_type="isbn" SHALL raise InvalidIsbnError.

        **Validates: Requirements 1.3**
        """
        provider = MockMetadataProvider()
        use_case = SearchBookMetadata(metadata_provider=provider)
        request = SearchBookMetadataRequest(query=isbn_string, search_type="isbn")

        with pytest.raises(InvalidIsbnError):
            use_case.execute(request)

    @given(
        query=st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
        result_count=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=100)
    def test_text_search_result_size_bounded(self, query: str, result_count: int) -> None:
        """Property 3: Text search result size bounded.

        For any non-empty text query and any MetadataProvider implementation that
        returns a list, the result list returned by SearchBookMetadata SHALL contain
        at most 10 items.

        **Validates: Requirements 2.1**
        """
        # Generate a list of BookMetadata results of variable length
        results = [
            BookMetadata(title=f"Book {i}")
            for i in range(result_count)
        ]
        provider = MockMetadataProvider(text_results=results)
        use_case = SearchBookMetadata(metadata_provider=provider)
        request = SearchBookMetadataRequest(query=query, search_type="text")

        actual = use_case.execute(request)
        assert len(actual) <= 10

    @given(metadata_list=st.lists(book_metadata_strategy(), min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_all_results_contain_non_empty_title(
        self, metadata_list: list[BookMetadata]
    ) -> None:
        """Property 4: All results contain a non-empty title.

        For any successful metadata search (ISBN or text), every BookMetadata object
        in the result list SHALL have a non-empty title field, and SHALL include all
        schema fields (title, author, genres, description, pages, isbn) even when
        their values are None/empty.

        **Validates: Requirements 2.3, 7.5**
        """
        provider = MockMetadataProvider(text_results=metadata_list)
        use_case = SearchBookMetadata(metadata_provider=provider)
        request = SearchBookMetadataRequest(query="test query", search_type="text")

        results = use_case.execute(request)

        for result in results:
            # Non-empty title
            assert result.title, f"Expected non-empty title, got: '{result.title}'"
            assert result.title.strip(), f"Title is whitespace-only: '{result.title}'"

            # All schema fields are present (they exist as attributes)
            assert hasattr(result, "title")
            assert hasattr(result, "author")
            assert hasattr(result, "genres")
            assert hasattr(result, "description")
            assert hasattr(result, "pages")
            assert hasattr(result, "isbn")

    @given(error_message=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_provider_error_propagation(self, error_message: str) -> None:
        """Property 5: Provider error propagation.

        For any MetadataProviderError raised by the MetadataProvider during search
        execution, the SearchBookMetadata use case SHALL NOT catch or suppress the
        exception — it SHALL propagate to the caller unchanged.

        **Validates: Requirements 4.1**
        """
        error = MetadataProviderError(message=error_message)
        provider = MockMetadataProvider(error=error)
        use_case = SearchBookMetadata(metadata_provider=provider)

        # Test with text search
        request = SearchBookMetadataRequest(query="any query", search_type="text")
        with pytest.raises(MetadataProviderError) as exc_info:
            use_case.execute(request)
        assert exc_info.value is error
        assert exc_info.value.message == error_message

        # Test with ISBN search (valid ISBN so it reaches the provider)
        request_isbn = SearchBookMetadataRequest(query="9780143120537", search_type="isbn")
        with pytest.raises(MetadataProviderError) as exc_info:
            use_case.execute(request_isbn)
        assert exc_info.value is error
        assert exc_info.value.message == error_message
