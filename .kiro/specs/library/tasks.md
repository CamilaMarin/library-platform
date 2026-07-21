# Implementation Plan: Library (Books, Copies & Reader)

## Overview

Implements personal library management (Books, Copies, Search, Import, Reader). Depends on `authentication` for `user_id`. Reading selection has its own spec.

## Tasks

- [ ] 1. Domain model: `Book`, `Copy` entities with type-based invariants and Book/Copy separation _(Req 1)_
- [ ] 2. `CreateBook` use case + `POST /books` endpoint (metadata only) _(Req 1.1)_
- [ ] 3. `CreateCopy` use case + `POST /copies` endpoint — physical (metadata+status) or digital (encrypted upload) _(Req 1.2, 1.3, 1.4)_
- [ ] 4. `EditBook`, `EditCopy`, `DeleteBook`, `DeleteCopy` use cases + endpoints _(Req 1.5)_
- [ ] 5. `ImportBookMetadata` use case — autocomplete from external source via `MetadataProvider` interface _(Req 2)_
- [ ] 6. `SearchBooks` use case — personal library + group shared library (metadata only, never file_ref) _(Req 3)_
- [ ] 7. Domain model: `ReadingProgress`, `Bookmark`, `Note` entities _(Req 4)_
- [ ] 8. `OpenReader` use case + `GET /copies/{id}/file` endpoint — validate ownership, serve file _(Req 4.1, 4.2)_
- [ ] 9. `SaveReadingProgress` use case + progress endpoints _(Req 4.3)_
- [ ] 10. Bookmark CRUD use cases + endpoints _(Req 4.4)_
- [ ] 11. Note CRUD use cases + endpoints _(Req 4.5)_
- [ ] 12. Domain + integration tests: ownership enforcement, search isolation, reader access, no file_ref leakage _(Req 1-4)_

## Task Dependency Graph
```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2, 7] },
    { "wave": 3, "tasks": [3, 5, 6] },
    { "wave": 4, "tasks": [4, 8] },
    { "wave": 5, "tasks": [9, 10, 11] },
    { "wave": 6, "tasks": [12] }
  ]
}
```

## Notes

- Requires `authentication` module's `User` and `FamilyGroup` entities.
- Reading selection (draw/sorteo) is in its own spec: `.kiro/specs/reading-selection/`.
- Task 5 requires a `MetadataProvider` interface (adr/0017) — implementation can start with Open Library.
- Task 8's ownership check is the same invariant validated in clubs (cross-context reading turn). Keep in sync.
- Reader data (tasks 9-11) is personal data — must integrate with Privacy module's audit log.
