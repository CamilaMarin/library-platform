# Design — Reader (EPUB/PDF)

Source: `docs/architecture/architecture.md`, `docs/domain/entities.md`.

### Referenced ADRs
- `adr/0014-integrated-reader-mvp.md` — Integrated EPUB/PDF reader in MVP
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation
- `adr/0017-cloud-agnostic-abstractions.md` — All infrastructure behind abstractions

## Overview

Implements an integrated EPUB/PDF reader with progress persistence. The reader only serves files to their authenticated owner. MVP scope is limited to rendering + progress tracking; bookmarks and notes are v1.

⚠️ **HIGH TECHNICAL RISK**: epub.js CFI positioning, PDF.js integration, browser memory with large files, mobile viewport handling.

## Architecture

The reader spans two layers:

**Backend** (within Library bounded context):
```
interface/   → file serving endpoint, progress endpoints
application/ → OpenReader, SaveReadingProgress use cases
domain/      → ReadingProgress entity
infrastructure/ → FileStorage (MinIO/S3), Postgres
```

**Frontend**:
```
components/  → EpubReader (epub.js wrapper), PdfReader (PDF.js wrapper)
hooks/       → useReadingProgress (auto-save logic)
```

## Components and Interfaces

- **ReadingProgress** (entity): user_id, copy_id, position (CFI for EPUB, page number for PDF), percentage, last_read_at.
- **OpenReader** (use case): validates `copy.user_id == request.user_id`, then streams the file from FileStorage.
- **SaveReadingProgress** (use case): upserts progress for the user+copy pair.

Endpoints:
- `GET /copies/{id}/file` — serve encrypted file (owner only, streamed)
- `GET /copies/{id}/progress` — get last saved progress
- `PUT /copies/{id}/progress` — save/update progress

## Data Models

```
ReadingProgress(id, user_id, copy_id, position, percentage, last_read_at)
```

- `position`: string field — CFI string for EPUB (e.g., `epubcfi(/6/4!/4/2/1:0)`), page number as string for PDF (e.g., `"42"`).
- `percentage`: float 0.0–1.0 representing overall progress.

## Correctness Properties

### Property 1: Ownership gate
`GET /copies/{id}/file` returns the file content ONLY when `request.user_id == copy.user_id`. All other cases return `403 Forbidden`.
**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Progress isolation
`ReadingProgress` records can only exist where `progress.user_id == copy.user_id` — a user cannot have progress on a copy they don't own.
**Validates: Requirements 2.1**

### Property 3: Idempotent progress save
`PUT /copies/{id}/progress` with the same position is idempotent — it updates `last_read_at` but doesn't create duplicate records.
**Validates: Requirements 2.3**

### Property 4: Format-appropriate positioning
EPUB files use CFI-based position strings. PDF files use page-number-based position strings. The system never mixes formats.
**Validates: Requirements 2.4**

## Error Handling

- Attempt to open a file not owned by the requester → `403 Forbidden` (never `404`, to avoid leaking existence).
- File missing from storage (corruption/deletion) → `500 Internal Server Error` with structured error, logged for investigation.
- Unsupported file format in progress save (neither EPUB CFI nor PDF page) → `422 Unprocessable Entity`.
- Progress save for a physical copy → `422 invalid_copy_type` (progress only applies to digital copies).
- File too large for browser rendering → handled client-side with loading states; backend streams regardless of size.

## Testing Strategy

- Domain unit tests: ReadingProgress entity invariants (user must own copy, position format validation).
- Integration tests: `GET /copies/{id}/file` — owner gets 200 with file content, non-owner gets 403.
- Integration tests: progress CRUD — save, retrieve, update, verify idempotency.
- Security tests: exhaustive attempt to access another user's file via every relevant endpoint.
- Frontend manual testing checklist:
  - [ ] EPUB renders and paginates correctly
  - [ ] PDF renders page by page
  - [ ] Progress auto-saves on page turn
  - [ ] Progress restores on reopen
  - [ ] Large files (>50MB) don't crash the browser
  - [ ] Mobile viewport handles reading view
