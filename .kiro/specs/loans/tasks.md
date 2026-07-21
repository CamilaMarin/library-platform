# Implementation Plan: Loans

## Overview

Implements physical-book loan tracking. Depends on `library` for `Copy` entities.

## Tasks

- [ ] 1. Domain model: `Loan` entity with a hard constraint that `copy.type == physical` _(Req 1.1)_
- [ ] 2. `RegisterLoan` use case + `POST /copies/{id}/loans` endpoint, rejecting digital copies with a clear error _(Req 1.1, 1.3)_
- [ ] 3. Copy status transition to `on_loan` on loan creation, with optional estimated return date _(Req 1.2)_
- [ ] 4. `RegisterReturn` use case + `PATCH /loans/{id}/return` endpoint, reverting copy status to `available` _(Req 1.2)_
- [ ] 5. Integration test confirming no endpoint under `/loans` ever accepts or returns a digital `file_ref` _(Req 1.3)_

## Task Dependency Graph
```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2] },
    { "wave": 3, "tasks": [3] },
    { "wave": 4, "tasks": [4] },
    { "wave": 5, "tasks": [5] }
  ]
}
```

## Notes

- Requires `library` module's `Copy` entity and `type` field to exist first.
- This module deliberately has no digital equivalent — see `clubs` spec's ReadingTurn instead.
- Uses status value `on_loan` (not "unavailable") consistently with Library's Copy.status enum.
