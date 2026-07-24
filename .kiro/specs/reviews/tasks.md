# Implementation Plan: Reviews

## Overview

Implements book reviews with explicit visibility control (`private | shared` + `shared_with`). Depends on `authentication` (groups), `library` (books), and `clubs` (for club membership verification).

## Tasks

- [ ] 1. Domain model: `Review` entity with visibility invariants (private → null shared_with; shared → explicit target) _(Req 1.1, 1.2, 1.3)_
- [ ] 2. `CreateReview` use case + `POST /reviews` endpoint, enforcing explicit visibility choice _(Req 1.1, 1.2, 1.3, 1.5)_
- [ ] 3. `EditReview` / `DeleteReview` use cases + endpoints (author-only) _(Req 1.4)_
- [ ] 4. `ListReviews` use case + `GET /books/{id}/reviews` endpoint with access control filter _(Req 2.1, 2.2, 2.3)_
- [ ] 5. Integration with Privacy module: reviews in ARCO export, deleted on cancellation _(Req 2.3)_
- [ ] 6. Domain + integration tests: visibility invariant, access control, privacy integration _(Req 1, 2)_

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

- Requires `authentication` module's group membership data for verifying `shared_with_type = group` access.
- Requires `clubs` module's club membership data for verifying `shared_with_type = club` access.
- Reviews are personal data — must integrate with Privacy module's audit log and ARCO flows.
- No review is ever "public" — the most broad sharing is to a specific group or club.
