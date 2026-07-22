# Implementation Plan: Library (Books, Copies & Search)

## Overview

Implements personal library management (Books, Copies, Search, Import). Depends on `authentication` for `user_id`. Reading selection and the integrated reader have their own specs.

## Tasks

- [ ] 1. Domain model: `Book`, `Copy` entities with type-based invariants and Book/Copy separation _(Req 1)_
- [ ] 2. `CreateBook` use case + `POST /books` endpoint (metadata only) _(Req 1.1)_
- [ ] 3. `CreateCopy` use case + `POST /copies` endpoint — physical (metadata+status) or digital (encrypted upload) _(Req 1.2, 1.3, 1.4)_
- [ ] 4. `EditBook`, `EditCopy`, `DeleteBook`, `DeleteCopy` use cases + endpoints _(Req 1.5)_
- [ ] 5. `ImportBookMetadata` use case — autocomplete from external source via `MetadataProvider` interface _(Req 2)_
- [ ] 6. `SearchBooks` use case — personal library + group shared library (metadata only, never file_ref) _(Req 3)_
- [ ] 7. Domain + integration tests: ownership enforcement, search isolation, no file_ref leakage _(Req 1-3)_

## Task Dependency Graph
```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2] },
    { "wave": 3, "tasks": [3, 5, 6] },
    { "wave": 4, "tasks": [4] },
    { "wave": 5, "tasks": [7] }
  ]
}
```

## Notes

- Requires `authentication` module's `User` and `FamilyGroup` entities.
- Reading selection (draw/sorteo) is in its own spec: `.kiro/specs/reading-selection/`.
- Integrated reader is in its own spec: `.kiro/specs/reader/`.
- Task 5 requires a `MetadataProvider` interface (adr/0017) — implementation can start with Open Library.
- Bookmarks and notes are deferred to v1 (reader-extras) per `docs/roadmap.md`.
