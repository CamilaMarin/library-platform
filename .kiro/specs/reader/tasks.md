# Implementation Plan: Reader (EPUB/PDF)

## Overview

Implements the integrated EPUB/PDF reader with progress persistence. MVP scope: file serving + ReadingProgress only. Bookmarks and notes are v1. Depends on `library` (Copy entity, FileStorage) and `authentication` (user_id).

⚠️ HIGH TECHNICAL RISK: epub.js CFI pagination, PDF.js integration, browser memory management.

## Tasks

- [x] 1. Domain model: `ReadingProgress` entity with ownership and format invariants _(Req 2.1, 2.4)_
- [x] 2. `OpenReader` use case + `GET /copies/{id}/file` endpoint — validate ownership, stream file from FileStorage _(Req 1.1, 1.2, 1.3, 1.5)_
- [x] 3. `SaveReadingProgress` use case + `PUT /copies/{id}/progress` endpoint (upsert) _(Req 2.1, 2.3)_
- [x] 4. `GET /copies/{id}/progress` endpoint — retrieve last saved position _(Req 2.2)_
- [x] 5. Frontend: PDF.js reader component with page-based progress auto-save _(Req 3.2, 3.3, 3.4)_
- [x] 6. Frontend: epub.js reader component with CFI-based progress auto-save _(Req 3.1, 3.3, 3.4)_
- [x] 7. Integration + security tests: ownership enforcement, progress isolation, no file_ref leakage _(Req 1-3)_

## Task Dependency Graph
```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2, 3, 4] },
    { "wave": 3, "tasks": [5, 6] },
    { "wave": 4, "tasks": [7] }
  ]
}
```

## Notes

- Requires `library` module's `Copy` entity and `FileStorage` interface to exist (from M3).
- Task 5 (PDF.js) should be implemented first — simpler than EPUB, page-based progress.
- Task 6 (epub.js) is the highest-risk task. CFI positioning varies across EPUB structures. Accept imperfect pagination for MVP.
- Bookmarks and notes are explicitly deferred to v1 per `docs/roadmap.md`.
- ReadingProgress is personal data — must integrate with Privacy module's AuditLog.
- If epub.js proves too unstable, the fallback is to launch MVP with PDF-only reader and add EPUB in a follow-up.
