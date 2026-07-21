# Implementation Plan: Reading Selection (Sorteo)

## Overview

Implements filtered random draw and pick-by-turn modes for family groups. Depends on `library` (Book/Copy entities) and `authentication` (groups).

## Tasks

- [ ] 1. Domain model: `Draw` entity, availability validation logic (physical: available copy; digital: owned copy) _(Req 1.1, 1.3, 1.4, 1.5)_
- [ ] 2. `RunReadingDraw` use case: filter books by genre, max pages, unread, then validate availability for all participants _(Req 1.1, 1.3)_
- [ ] 3. `POST /groups/{id}/draws` endpoint — draw results show source library, never file_ref _(Req 1.2, 1.6)_
- [ ] 4. `GET /groups/{id}/draws` endpoint — draw history _(Req 1.2)_
- [ ] 5. Domain model: `TurnHistory` entity _(Req 2)_
- [ ] 6. `PickByTurn` use case with fair rotation logic _(Req 2.1, 2.2)_
- [ ] 7. Integration tests: availability validation (physical available/on_loan, digital owned/not), empty result, no file_ref leakage _(Req 1, 2)_

## Task Dependency Graph
```json
{
  "waves": [
    { "wave": 1, "tasks": [1, 5] },
    { "wave": 2, "tasks": [2, 6] },
    { "wave": 3, "tasks": [3, 4] },
    { "wave": 4, "tasks": [7] }
  ]
}
```

## Notes

- Requires `library` module's Book, Copy entities and Loans module's status transitions.
- Requires `authentication` module's FamilyGroup and membership data.
- Availability check must query Copy.status in real time (a copy lent out after draw setup should be excluded).
- This feature lives in its own spec per `adr/0013-reading-selection-dedicated-spec.md` but shares the Library bounded context at implementation level.
