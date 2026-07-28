# Design — Reading Status

Source: `docs/domain/entities.md`, `docs/architecture/database.md`.

### Referenced ADRs
- `adr/0015-book-copy-separation.md` — status lives on Book, not Copy
- `adr/0003-ley-21719-compliance.md` — personal data: audit + ARCO

## Overview

Adds a `ReadingStatus` entity to the Library bounded context with key
`(user_id, book_id)`. The frontend gains a shelf view that renders books
as vertical spines grouped by status, toggleable with the existing list view.

## Architecture

Bounded context: **Library** (no new context needed).

```
interface/   → books_router.py (2 new endpoints)
application/ → set_reading_status.py, get_reading_statuses.py, protocols.py (new protocol)
domain/      → entities.py (ReadingStatus entity + ReadingStatusValue enum)
infrastructure/ → models.py (ReadingStatusModel), repositories.py (SqlReadingStatusRepository)
```

## Data Model

```
ReadingStatus(
  id          UUID PK,
  user_id     UUID FK → users.id ON DELETE CASCADE,
  book_id     UUID FK → books.id ON DELETE CASCADE,
  status      VARCHAR(20) NOT NULL,   -- want_to_read | reading | read | dnf
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
  UNIQUE (user_id, book_id)
)
```

Indexes: `(user_id)` for fast per-user fetch. The unique constraint covers
the upsert requirement (Req 1.3).

## Domain Entity

```python
class ReadingStatusValue(str, Enum):
    WANT_TO_READ = "want_to_read"
    READING      = "reading"
    READ         = "read"
    DNF          = "dnf"

@dataclass
class ReadingStatus:
    user_id:    UUID
    book_id:    UUID
    status:     ReadingStatusValue
    id:         UUID = field(default_factory=uuid4)
    updated_at: datetime = field(default_factory=_utcnow)
```

No invariants beyond valid enum value (enforced by the enum itself).

## API Endpoints

```
PUT    /books/{book_id}/status   — upsert status for authenticated user
DELETE /books/{book_id}/status   — remove status (returns 204)
GET    /books/statuses           — list all (book_id, status) for user
```

Request body for PUT:
```json
{ "status": "reading" }
```

Response for GET:
```json
[
  { "book_id": "...", "status": "reading", "updated_at": "..." },
  ...
]
```

## Frontend Architecture

### New components
- `BookSpine` — single vertical spine. Props: `book`, `status`, `onStatusChange`.
  Renders title rotated -90°, color from status palette, brass bottom accent.
  Click → opens inline status popover.
- `BookShelf` — one shelf row. Props: `label`, `books`, `statuses`, `onStatusChange`.
  Renders spines side by side on a teak "table" line.

### Library page changes
- Add `viewMode: "list" | "shelf"` state, initialized from `localStorage`.
- Fetch `/books/statuses` in parallel with `/books` when mounting.
- Toggle button (LayoutList / Rows icons from Lucide) in the page header.
- Shelf view groups books by status; unclassified books in a final shelf.
- List view: unchanged, but adds a small status badge/pill per book row
  so users can change status from both views.

### Status color palette (from existing design tokens)
```
reading      → var(--color-reading)   #2E5C3E  dark green
read         → var(--color-walnut)    #2C1F14  dark walnut
want_to_read → var(--color-teak)      #8B5E3C  medium brown
dnf          → var(--color-mahogany)  #4A2E1A  reddish brown
unclassified → var(--color-aged)      #E0D0AE  light parchment
```

## Correctness Properties

### Property 1: One status per user-book pair
At most one `ReadingStatus` record exists for any `(user_id, book_id)` pair.
**Validates: Requirement 1.3**

### Property 2: Status ownership
`PUT /books/{id}/status` and `DELETE /books/{id}/status` only affect the
record whose `user_id` matches the authenticated user.
**Validates: Requirement 1.5**

### Property 3: No status leakage
`GET /books/statuses` returns only records where `user_id` equals the
authenticated user — never another user's statuses.
**Validates: Requirement 2.1**

## Privacy (Ley 21.719)

Reading status is personal data (reveals reading habits). It must be:
- Included in `GET /users/me/export` (ARCO access right) — extend `ExportUserData`.
- Deleted on `DELETE /users/me` (ARCO cancellation) — `ON DELETE CASCADE` on `user_id`.
  The cascade in the DB handles this automatically; no use-case change needed.

## Error Handling

- `PUT` with unknown status value → `422 invalid_status`.
- `DELETE` when no status exists → `204` (idempotent, no error).
- `PUT`/`DELETE` for a book_id not in user's library → `404 book_not_found`.
