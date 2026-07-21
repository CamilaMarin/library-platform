# Design — Reading Selection (Sorteo)

Source: `docs/architecture/architecture.md`, `docs/domain/entities.md`.

### Referenced ADRs
- `adr/0008-reading-selection-availability.md` — Availability rule
- `adr/0013-reading-selection-dedicated-spec.md` — Dedicated specification
- `adr/0001-no-shared-file-storage.md` — No file sharing
- `adr/0009-digital-books-isolation.md` — Digital books isolation
- `adr/0015-book-copy-separation.md` — Book/Copy separation

## Overview

Implements joint reading selection for family groups: a random draw with filters (genre, pages, availability, unread) and an alternative pick-by-turn mode. The availability rule ensures fairness by requiring every participant to have authorized access to the book.

## Architecture

Clean Architecture. Lives within the **Library** bounded context functionally (uses Book/Copy entities) but has its own spec due to complexity.

```
interface/   → REST endpoints (draws)
application/ → use cases (RunReadingDraw, PickByTurn)
domain/      → Draw entity, availability validation logic
infrastructure/ → Postgres
```

## Components and Interfaces

- **Draw**: group_id, participants[], filters (genre, max_pages, unread_only, availability_check), result_book_id, result_source_user_id, timestamp.
- **TurnHistory**: group_id, user_id, last_pick_date.

Use cases: `RunReadingDraw`, `PickByTurn`.

Endpoints:
- `POST /groups/{id}/draws` — execute draw (filters + participants in body)
- `GET /groups/{id}/draws` — draw history

## Data Models

```
Draw(id, group_id, filters_json, participants_json, result_book_id, result_source_user_id, timestamp)
TurnHistory(id, group_id, user_id, last_pick_date)
```

## Correctness Properties

### Property 1: Availability rule — physical books
A book can only appear as a draw candidate if EVERY selected participant has authorized access. Physical book: participant owns a Copy with `type == physical` and `status == available`.
**Validates: Requirements 1.3, 1.4**

### Property 2: Availability rule — digital books
Digital book: participant owns a Copy with `type == digital` (ownership is sufficient; no availability check beyond ownership since digital copies can't be "on loan").
**Validates: Requirements 1.3, 1.5**

### Property 3: No file exposure in results
Draw results never expose `file_ref` of any Copy.
**Validates: Requirements 1.6**

### Property 4: Source attribution without access
The result's `source_user_id` indicates whose library the book came from (for attribution), but does not imply file access.
**Validates: Requirements 1.2**

### Property 5: Deterministic turn rotation
Pick-by-turn rotation is deterministic: next picker is the member with the oldest (or null) `TurnHistory.last_pick_date`.
**Validates: Requirements 2.2**

## Error Handling

- Draw with filters matching zero books → `200` with empty result and suggestion to relax filters (not an error).
- Draw requested by a user not in the specified group → `403 forbidden`.
- Pick-by-turn when all members have picked equally recently → any member can pick (tie-breaking by earliest join date or random).

## Testing Strategy

- Domain unit tests: availability validation for physical (available vs on_loan), digital (owned vs not), mixed scenarios.
- Integration tests: draw with each filter combination, draw with impossible filters (empty result), turn rotation fairness.
- Security test: draw result never includes `file_ref` in response payload.
- Cross-context: verify that Copy.status from Loans module correctly affects draw availability.
