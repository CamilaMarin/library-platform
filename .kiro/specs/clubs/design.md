# Design — Clubs & Reading Turns

Source: `docs/architecture/architecture.md`, `docs/domain/entities.md`.

### Referenced ADRs
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0006-no-connected-groups-mvp.md` — Clubs only within a single family group in MVP
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation

## Overview

This module coordinates book clubs within a single family group: active book, discussion date, spoiler-safe comments, and digital reading turns. Each participant must already own their own copy — no file is ever transferred between accounts.

## Architecture

Clean Architecture, bounded context **Community**:

```
interface/   → REST endpoints (clubs, comments, reading turns)
application/ → use cases (see Components below)
domain/      → Club, ReadingTurn, Comment entities
infrastructure/ → Postgres; read-only query into Library context's Copy ownership (id + status only, never file_ref)
```

## Components and Interfaces

- **Club** (aggregate root): group_id (single group), active_book_id, discussion_date.
- **ReadingTurn** (entity within Club): current_user_id, comments[].
- **Comment**: turn_id, user_id, text, is_spoiler (default: false).

Use cases: `CreateClub`, `SetActiveBook`, `PostComment`, `ActivateReadingTurn`.

Endpoints:
- `POST /clubs`, `GET /clubs/{id}`, `PATCH /clubs/{id}/active-book`
- `POST /clubs/{id}/comments`
- `POST /clubs/{id}/reading-turns`, `PATCH /reading-turns/{id}`

## Data Models

```
Club(id, group_id, active_book_id, discussion_date)
ReadingTurn(id, club_id, book_id, current_user_id)
Comment(id, turn_id, user_id, text, is_spoiler, created_at)
```

> Note: `group_id` is singular (not an array). Multi-group clubs removed from MVP per adr/0006.

## Correctness Properties

- `ActivateReadingTurn` for a `(user_id, book_id)` pair succeeds only if that user owns a `Copy` of that book (checked via Library context's ownership query — never by copying or caching `file_ref`).
- A `Club.group_id` always references an existing `FamilyGroup`.
- `Comment.is_spoiler` defaults to `false`; users must explicitly mark spoiler content.

## Error Handling

- Attempt to activate a reading turn without an owned copy → `409 conflict`, response includes a prompt to add the book to the user's own library.
- Attempt to create a club referencing a non-existent group → `404 not_found`.
- Setting an active book not present in any member's library → allowed (members may still be planning to acquire it), but reading turns cannot activate until ownership exists.

## Testing Strategy

- Domain unit tests: turn activation invariant, spoiler default (false) behavior.
- Integration tests: create club (single group only), set active book, post comment with/without spoiler flag, activate/deny reading turn based on ownership.
- Cross-context test: verify the Library ownership query never returns `file_ref` to the Community context.
