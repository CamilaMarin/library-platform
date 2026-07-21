# Implementation Plan: Clubs & Reading Turns

## Overview

Implements book clubs, comments, and digital reading turns within a single family group. Depends on `authentication` (groups) and `library` (copy ownership).

## Tasks

- [ ] 1. Domain model: `Club`, `ReadingTurn`, `Comment` entities — `Club.group_id` is singular (not array) _(Req 1.1, 1.2, 2.1)_
- [ ] 2. `CreateClub` use case + `POST /clubs` endpoint (single group only) _(Req 1.1)_
- [ ] 3. `SetActiveBook` use case + endpoint _(Req 1.2)_
- [ ] 4. `PostComment` use case + endpoint with `is_spoiler` flag (default: false) _(Req 1.3)_
- [ ] 5. `ActivateReadingTurn` use case validating copy ownership before activation _(Req 1.4, 2.1, 2.2)_
- [ ] 6. Integration test: turn activation without an owned copy is rejected, and no endpoint returns another member's `file_ref` _(Req 1.4, 2.2)_

## Task Dependency Graph
```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2] },
    { "wave": 3, "tasks": [3, 4] },
    { "wave": 4, "tasks": [5] },
    { "wave": 5, "tasks": [6] }
  ]
}
```

## Notes

- Task 5 requires the `library` module's copy-ownership query to be available (read-only, id/status only — never `file_ref`).
- Multi-group clubs are explicitly out of scope for MVP per `adr/0006-no-connected-groups-mvp.md`.
- `Comment.is_spoiler` defaults to `false` — users must explicitly mark spoiler content.
