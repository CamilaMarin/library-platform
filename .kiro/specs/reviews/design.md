# Design — Reviews

Source: `docs/architecture/database.md`, `docs/domain/entities.md`.

### Referenced ADRs
- `adr/0007-review-visibility-model.md` — Visibility model: private | shared + shared_with
- `adr/0003-ley-21719-compliance.md` — Reviews are personal data

## Overview

Implements book reviews with explicit visibility control. Every review is either private (author only) or shared with a specific group or club. No review is ever publicly visible.

## Architecture

Clean Architecture, bounded context **Reviews**:

```
interface/   → REST endpoints (reviews)
application/ → use cases (CreateReview, EditReview, DeleteReview, ListReviews)
domain/      → Review entity with visibility invariants
infrastructure/ → Postgres
```

## Components and Interfaces

- **Review** (aggregate root): user_id, book_id, rating (integer 1–5), text, visibility, shared_with_type, shared_with_id.

Use cases: `CreateReview`, `EditReview`, `DeleteReview`, `ListReviews` (filtered by visibility/access).

Endpoints:
- `POST /reviews`
- `PATCH /reviews/{id}`
- `DELETE /reviews/{id}`
- `GET /books/{id}/reviews` (returns only reviews the requester is authorized to see)

## Data Models

```
Review(id, user_id, book_id, rating[integer 1-5], text, visibility[private|shared], shared_with_type[group|club|null], shared_with_id[nullable], created_at, updated_at)
```

## Correctness Properties

- `Review.visibility == 'private'` implies `shared_with_type IS NULL AND shared_with_id IS NULL`.
- `Review.visibility == 'shared'` implies `shared_with_type IS NOT NULL AND shared_with_id IS NOT NULL`.
- A `shared` review is only served to users who are members of the specified group or club at query time.
- A `private` review is only served to its `user_id` (the author).
- No review is ever served without an explicit access check against the requester's memberships.

## Error Handling

- Create review with `visibility = shared` but no `shared_with` → `422 invalid_visibility_target`.
- Edit review by non-author → `403 forbidden`.
- Request reviews for a book the requester has no authorized access to see shared reviews for → returns only their own private reviews (empty shared set, not an error).

## Testing Strategy

- Domain unit tests: visibility invariant (private → null shared_with, shared → non-null shared_with).
- Integration tests: create private review → only author sees it; create shared review → only group/club members see it; non-member gets empty.
- Access control test: user leaves a group → previously-shared review in that group becomes invisible to them.
- Privacy integration: verify reviews appear in ARCO export and are deleted on account cancellation.
