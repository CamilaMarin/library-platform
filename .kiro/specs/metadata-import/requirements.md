# Requirements Document

## Introduction

Metadata Import allows users to autocomplete book metadata (title, author, pages, genres, ISBN, description) from external sources when adding a book to their library. Instead of manually typing all fields, users can search by ISBN or title and have the system prefill the form with publicly available book information.

The MVP uses Open Library API as the external source. The architecture supports adding additional providers (e.g., Google Books) later via the `MetadataProvider` protocol (ADR-0017). This feature lives within the Library bounded context as a use case (ADR-0011).

This is a convenience feature — it never blocks manual book creation. No personal data is transmitted to external APIs, and no external API responses are persisted in the database.

## Glossary

- **Metadata_Import_Service**: The application-layer use case that coordinates searching for book metadata from external providers and returning results to the caller.
- **MetadataProvider**: A protocol (interface) defined in the application layer that abstracts access to external book metadata sources. Implementations live in `library/infrastructure/`.
- **Open_Library_Adapter**: The infrastructure-layer implementation of `MetadataProvider` that queries the Open Library API.
- **Book_Metadata**: A value object containing the set of fields returned by a metadata search: title, author, genres, description, pages, and ISBN.
- **Search_Query**: The user-supplied input used to find books externally — either an ISBN string or a free-text title/author combination.

## Requirements

### Requirement 1: Search by ISBN

**User Story:** As a user adding a book, I want to search by ISBN and have the system return matching book metadata, so that I can autocomplete the form without typing everything manually.

#### Acceptance Criteria

1. WHEN a user submits a Search_Query containing a valid ISBN, THE Metadata_Import_Service SHALL query the MetadataProvider and return a single Book_Metadata result matching that ISBN.
2. WHEN a user submits a Search_Query containing an ISBN that has no match in the external source, THE Metadata_Import_Service SHALL return an empty result set.
3. WHEN a user submits a Search_Query containing a malformed ISBN (not 10 or 13 digits after removing hyphens), THE Metadata_Import_Service SHALL reject the query with a validation error.

### Requirement 2: Search by Title/Author

**User Story:** As a user adding a book, I want to search by title or author name and select from matching results, so that I can find the correct edition and autocomplete metadata.

#### Acceptance Criteria

1. WHEN a user submits a Search_Query containing a free-text title or author string, THE Metadata_Import_Service SHALL query the MetadataProvider and return a list of Book_Metadata results (maximum 10 results).
2. WHEN a user submits a Search_Query containing a free-text string that yields no matches, THE Metadata_Import_Service SHALL return an empty result set.
3. THE Metadata_Import_Service SHALL return results containing at minimum: title and author for each match, with pages, genres, description, and ISBN populated when available from the external source.

### Requirement 3: MetadataProvider Abstraction

**User Story:** As a developer, I want external metadata sources accessed through a protocol interface, so that additional providers can be added without modifying the application layer.

#### Acceptance Criteria

1. THE MetadataProvider protocol SHALL define a method for searching by ISBN that accepts a string and returns an optional Book_Metadata.
2. THE MetadataProvider protocol SHALL define a method for searching by text query that accepts a string and returns a list of Book_Metadata (maximum 10 items).
3. THE Open_Library_Adapter SHALL implement the MetadataProvider protocol using the Open Library API as its data source.
4. WHEN a new metadata source is required, THE system SHALL allow adding a new MetadataProvider implementation without modifying existing application-layer code.

### Requirement 4: Graceful Degradation

**User Story:** As a user, I want to still be able to add books manually when the external metadata service is unavailable, so that the core functionality is never blocked by an external dependency.

#### Acceptance Criteria

1. IF the MetadataProvider returns a network error or timeout, THEN THE Metadata_Import_Service SHALL return a structured error indicating the external service is unavailable.
2. IF the MetadataProvider is unavailable, THEN THE system SHALL continue to allow manual book creation via the existing `POST /books` endpoint without any degradation.
3. THE Open_Library_Adapter SHALL enforce a request timeout of no more than 5 seconds per external API call.

### Requirement 5: Editable Metadata Before Saving

**User Story:** As a user, I want to review and edit the autocompleted metadata before saving the book, so that I can correct inaccuracies or add missing information.

#### Acceptance Criteria

1. WHEN the Metadata_Import_Service returns Book_Metadata, THE system SHALL treat the result as a suggestion that the user can modify before submitting to `POST /books`.
2. THE system SHALL not automatically create a Book entity from imported metadata — book creation only occurs when the user explicitly submits the form.
3. THE system SHALL allow the user to override any field returned by the MetadataProvider before saving.

### Requirement 6: Privacy and Data Minimization

**User Story:** As a user, I want assurance that my personal data is never sent to external APIs, so that my privacy is preserved in compliance with Ley 21.719.

#### Acceptance Criteria

1. THE Metadata_Import_Service SHALL transmit only the Search_Query (ISBN or title/author text) to the external MetadataProvider — no user identifiers, tokens, or personal data.
2. THE system SHALL not persist external API responses in the database — metadata is used exclusively to prefill the client form.
3. THE system SHALL not log the content of external API responses that could be associated with a specific user request.

### Requirement 7: API Endpoint for Metadata Search

**User Story:** As a frontend developer, I want a REST endpoint to search for book metadata, so that the UI can offer autocomplete functionality in the book creation form.

#### Acceptance Criteria

1. THE system SHALL expose a `GET /books/metadata/search` endpoint that accepts a `query` parameter (the Search_Query) and an optional `type` parameter (`isbn` or `text`, defaulting to `text`).
2. WHEN the `type` parameter is `isbn`, THE endpoint SHALL invoke the ISBN search method of the Metadata_Import_Service.
3. WHEN the `type` parameter is `text`, THE endpoint SHALL invoke the text search method of the Metadata_Import_Service.
4. THE endpoint SHALL require authentication (valid JWT access token).
5. THE endpoint SHALL return results as a JSON array of Book_Metadata objects, each containing: title, author, genres, description, pages, and isbn (with null for unavailable fields).
