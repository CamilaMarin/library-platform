# Design — Library (Books, Copies & Reader)

Source: `docs/architecture/architecture.md`, `docs/architecture/database.md`, `docs/domain/entities.md`.

### Referenced ADRs
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation
- `adr/0010-search-in-library-module.md` — Search is part of Library
- `adr/0011-import-as-library-use-case.md` — Import is a Library use case
- `adr/0014-integrated-reader-mvp.md` — Integrated EPUB/PDF reader in MVP
- `adr/0015-book-copy-separation.md` — Book/Copy separation
- `adr/0017-cloud-agnostic-abstractions.md` — All infrastructure behind abstractions

## Overview

This module covers personal library management: Books (metadata), Copies (physical or digital, owned per user), search, metadata import, and an integrated EPUB/PDF reader with progress tracking, bookmarks, and notes. Digital files are strictly isolated per account.

Reading selection (sorteo) lives in its own spec: `.kiro/specs/reading-selection/`.

## Architecture

Clean Architecture, bounded context **Library**:

```
interface/   → REST endpoints (books, copies, reader, search)
application/ → use cases (see Components below)
domain/      → Book, Copy, ReadingProgress, Bookmark, Note entities; enforces per-user file isolation
infrastructure/ → Postgres, encrypted object storage (via FileStorage interface), external metadata API client (via MetadataProvider interface)
```

All external services accessed through abstractions (adr/0017): `FileStorage`, `MetadataProvider`.

## Components and Interfaces

- **Book** (catalog entity): title, author, genres, description, page_count, isbn.
- **Copy** (aggregate root, belongs to a User): type (physical | digital), file_ref (digital only), status (available | on_loan).
- **ReadingProgress**: user_id, copy_id, position, percentage, last_read_at.

> Note: Bookmark and Note entities are deferred to v1 (reader-extras). See `.kiro/specs/reader/` for the full reader spec.

Use cases:
- `CreateBook`, `CreateCopy`, `EditBook`, `EditCopy`, `DeleteBook`, `DeleteCopy`
- `SearchBooks` (personal + group library, metadata only)
- `ImportBookMetadata` (autocomplete from external source)
- `OpenReader` (validate ownership, serve file)
- `SaveReadingProgress`

Endpoints:
- `POST /books`, `GET /books?query=`, `PATCH /books/{id}`, `DELETE /books/{id}`
- `POST /copies`, `GET /copies/{id}`, `PATCH /copies/{id}`, `DELETE /copies/{id}`
- `GET /copies/{id}/file` (serve encrypted file to owner only)
- `GET /copies/{id}/progress`, `PUT /copies/{id}/progress`

## Data Models

```
Book(id, title, author, genres[], description, page_count, isbn)
Copy(id, user_id, book_id, type[physical|digital], file_ref, status[available|on_loan])
ReadingProgress(id, user_id, copy_id, position, percentage, last_read_at)
```

## Correctness Properties

### Property 1: Book exists without copies
A `Book` can exist without any associated Copies.
**Validates: Requirements 1.1**

### Property 2: File isolation
`Copy.file_ref` is only ever resolved when `request.user_id == Copy.user_id`; every other request path returns no file reference.
**Validates: Requirements 1.3**

### Property 3: Physical copy has no file
`Copy.type == physical` implies `file_ref IS NULL`, always.
**Validates: Requirements 1.4**

### Property 4: Reader data ownership
`ReadingProgress` can only exist for digital copies whose `user_id` matches the record's `user_id`.
**Validates: Requirements 4.2**

### Property 5: Group search isolation
Search results from the group library never expose `file_ref` of any copy.
**Validates: Requirements 3.3**

### Property 6: Metadata provider abstraction
`MetadataProvider` is accessed via an interface — the implementation is replaceable without domain changes.
**Validates: Requirements 2.2**

## Error Handling

- Digital upload exceeding size/format limits → `422 unsupported_file`, no partial storage write.
- Attempt to read `file_ref` for a Copy not owned by the requester → `403 forbidden`.
- Attempt to access reader data (progress/bookmarks/notes) for a non-owned copy → `403 forbidden`.
- Metadata autocomplete when external source is unavailable → graceful degradation (no autocomplete, user can still enter manually).
- Delete a Book that still has Copies → `409 conflict`, user must explicitly delete their copies first.

## Testing Strategy

- Domain unit tests: physical/digital invariants, Book can exist without Copies, Copy ownership validation.
- Integration tests: add book, add physical/digital copy as separate steps, edit/delete, metadata autocomplete fallback.
- Reader tests: open file (owner), reject open (non-owner), save/load progress, CRUD bookmarks, CRUD notes.
- Security test (required): attempt to fetch another user's digital `file_ref` via every relevant endpoint and assert `403`.
- Search test: verify group library search never leaks `file_ref`.
