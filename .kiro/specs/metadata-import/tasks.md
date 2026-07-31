# Implementation Plan: Metadata Import

## Overview

Implement a metadata autocomplete feature for the book creation form. Users can search by ISBN or free text to retrieve book metadata from the Open Library API, which prefills the form fields. The implementation follows Clean Architecture layers: domain value object → application protocol + use case → infrastructure adapter → interface endpoint → frontend UI.

## Tasks

- [x] 1. Domain layer — BookMetadata value object
  - [x] 1.1 Add `BookMetadata` frozen dataclass to `backend/app/library/domain/entities.py`
    - Define `BookMetadata` with fields: `title` (required str), `author` (optional str), `genres` (list[str], default empty), `description` (optional str), `pages` (optional int), `isbn` (optional str)
    - Use `@dataclass(frozen=True)` — this is a transient value object, not an entity
    - Add `field(default_factory=list)` for `genres`
    - _Requirements: 2.3, 3.1, 3.2_

- [x] 2. Application layer — protocol and use case
  - [x] 2.1 Add `MetadataProviderError` and `MetadataProvider` protocol to `backend/app/library/application/protocols.py`
    - Add `MetadataProviderError(Exception)` with a `message` attribute
    - Add `MetadataProvider` protocol with `search_by_isbn(isbn: str) -> BookMetadata | None` and `search_by_text(query: str, limit: int = 10) -> list[BookMetadata]`
    - Both methods document they raise `MetadataProviderError` on network failure
    - _Requirements: 3.1, 3.2, 3.4, 4.1_

  - [x] 2.2 Create `backend/app/library/application/search_book_metadata.py` with the `SearchBookMetadata` use case
    - Define `SearchBookMetadataRequest` dataclass with `query: str` and `search_type: str = "text"`
    - Implement `SearchBookMetadata` class with `__init__(self, metadata_provider: MetadataProvider)` and `execute(request) -> list[BookMetadata]`
    - Implement `_normalize_isbn(raw: str) -> str` (strip hyphens and spaces)
    - Implement `_validate_isbn(isbn: str) -> None` — raise `InvalidIsbnError` if not 10 or 13 digits
    - For text search: strip whitespace, return `[]` if empty, otherwise delegate to `search_by_text(query, limit=10)`
    - Define `InvalidIsbnError(ValueError)` with `isbn` attribute
    - Do NOT catch `MetadataProviderError` — let it propagate to the interface layer
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 4.1_

  - [x] 2.3 Write property test: ISBN normalization accepts valid formats (Property 1)
    - **Property 1: ISBN normalization accepts valid formats**
    - **Validates: Requirements 1.1, 1.3**
    - Use Hypothesis to generate strings of exactly 10 or 13 digit characters interspersed with arbitrary hyphens/spaces
    - Assert `_normalize_isbn` + `_validate_isbn` does not raise
    - File: `backend/tests/library/test_metadata_properties.py`

  - [x] 2.4 Write property test: Malformed ISBN rejection (Property 2)
    - **Property 2: Malformed ISBN rejection**
    - **Validates: Requirements 1.3**
    - Use Hypothesis to generate strings where, after removing hyphens/spaces, the result is not exactly 10 or 13 digits
    - Assert `SearchBookMetadata.execute(request)` raises `InvalidIsbnError`
    - File: `backend/tests/library/test_metadata_properties.py`

  - [x] 2.5 Write property test: Text search result size bounded (Property 3)
    - **Property 3: Text search result size bounded**
    - **Validates: Requirements 2.1**
    - Use Hypothesis to generate non-empty text queries with a mock `MetadataProvider` returning variable-length lists
    - Assert the use case result has at most 10 items
    - File: `backend/tests/library/test_metadata_properties.py`

  - [x] 2.6 Write property test: All results contain a non-empty title (Property 4)
    - **Property 4: All results contain a non-empty title**
    - **Validates: Requirements 2.3, 7.5**
    - Use Hypothesis to generate lists of `BookMetadata` objects
    - Assert every result has a non-empty `title` and all schema fields are present
    - File: `backend/tests/library/test_metadata_properties.py`

  - [x] 2.7 Write property test: Provider error propagation (Property 5)
    - **Property 5: Provider error propagation**
    - **Validates: Requirements 4.1**
    - Use Hypothesis to generate random `MetadataProviderError` messages
    - Mock provider to raise the error, assert it propagates through `execute()` unchanged
    - File: `backend/tests/library/test_metadata_properties.py`

- [x] 3. Checkpoint — Domain and application layer
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Infrastructure layer — OpenLibraryAdapter
  - [x] 4.1 Add `httpx` to backend dependencies
    - Add `httpx` to the project's requirements file (e.g., `requirements.txt` or equivalent)
    - _Requirements: 3.3, 4.3_

  - [x] 4.2 Create `backend/app/library/infrastructure/open_library_adapter.py`
    - Implement `OpenLibraryAdapter` class that satisfies the `MetadataProvider` protocol
    - `BASE_URL = "https://openlibrary.org"`, `TIMEOUT_SECONDS = 5.0`
    - Set custom `User-Agent: EntreLineas/1.0 (library-platform)` header
    - `search_by_isbn(isbn)`: GET `{BASE_URL}/isbn/{isbn}.json`, map response to `BookMetadata`, resolve author key via secondary request (fallback to `None`)
    - `search_by_text(query, limit=10)`: GET `{BASE_URL}/search.json?q={query}&limit={limit}&fields=title,author_name,isbn,number_of_pages_median,subject`, map results to `list[BookMetadata]`
    - Catch `httpx.TimeoutException`, `httpx.ConnectError`, and other `httpx` errors → raise `MetadataProviderError`
    - Handle unexpected JSON gracefully: log warning, return `None` or partial results
    - _Requirements: 3.3, 4.1, 4.3, 6.1_

- [x] 5. Interface layer — endpoint and schema
  - [x] 5.1 Add `BookMetadataResponse` schema to `backend/app/library/interface/schemas.py`
    - Pydantic model with: `title: str`, `author: str | None`, `genres: list[str]`, `description: str | None`, `pages: int | None`, `isbn: str | None`
    - _Requirements: 7.5_

  - [x] 5.2 Add `GET /books/metadata/search` endpoint to `backend/app/library/interface/books_router.py`
    - Declare the route BEFORE `/{book_id}` to avoid path parameter capture (same pattern as `/statuses`)
    - Accept query params: `query: str`, `type: str = "text"`
    - Require authentication via `Depends(get_current_user_id)`
    - Instantiate `OpenLibraryAdapter` and `SearchBookMetadata` use case
    - Map `InvalidIsbnError` → HTTP 422 with `{"detail": "invalid_isbn_format"}`
    - Map `MetadataProviderError` → HTTP 503 with `{"detail": "external_metadata_service_unavailable"}`
    - Return `list[BookMetadataResponse]`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 4.1, 6.1_

- [x] 6. Checkpoint — Backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Frontend — autocomplete UI in add book form
  - [x] 7.1 Add `BookMetadata` TypeScript type to `frontend/src/types/index.ts` (or equivalent)
    - Define interface matching the API response: `title`, `author`, `genres`, `description`, `pages`, `isbn`
    - _Requirements: 7.5_

  - [x] 7.2 Add metadata search helper function to `frontend/src/lib/api-client.ts` or a new `frontend/src/lib/metadata.ts`
    - Function `searchBookMetadata(query: string, type: "isbn" | "text"): Promise<BookMetadata[]>`
    - Calls `GET /books/metadata/search?query={query}&type={type}` via `apiGet`
    - _Requirements: 7.1_

  - [x] 7.3 Implement autocomplete UI in the add book form at `frontend/src/app/library/page.tsx`
    - Add a debounced search input (300ms) above or within the form that triggers metadata search
    - Display results in a dropdown/list for the user to select from
    - On selection, prefill form fields (title, author, isbn, genres, description, pages) with the metadata values
    - Allow the user to edit any prefilled field before submitting
    - Handle loading state and error state (503 → show message, don't block manual entry)
    - Handle empty results gracefully
    - _Requirements: 1.1, 2.1, 4.2, 5.1, 5.2, 5.3_

- [x] 8. Integration tests
  - [x] 8.1 Write integration tests for the `/books/metadata/search` endpoint
    - Test ISBN search happy path (mocked adapter) → 200 with result
    - Test malformed ISBN → 422 with `invalid_isbn_format`
    - Test text search happy path → 200 with results array
    - Test missing auth → 401
    - Test provider unavailable → 503 with `external_metadata_service_unavailable`
    - Test empty text query → 200 with empty array
    - File: `backend/tests/library/test_metadata_search_integration.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 4.1, 1.3_

- [x] 9. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The design uses Python (not pseudocode), so all backend code uses Python
- Frontend uses TypeScript/React (Next.js) as per the existing codebase
- `httpx` is a new dependency — it must be added before the adapter can be implemented
- The `/metadata/search` endpoint MUST be declared before `/{book_id}` in the router file to avoid route capture
- No database migrations needed — `BookMetadata` is a transient value object only

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["2.3", "2.4", "2.5", "2.6", "2.7", "4.1"] },
    { "id": 3, "tasks": ["4.2"] },
    { "id": 4, "tasks": ["5.1", "5.2"] },
    { "id": 5, "tasks": ["7.1", "7.2"] },
    { "id": 6, "tasks": ["7.3"] },
    { "id": 7, "tasks": ["8.1"] }
  ]
}
```
