# Tasks — Reading Status

## Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2] },
    { "wave": 3, "tasks": [3, 4] },
    { "wave": 4, "tasks": [5] },
    { "wave": 5, "tasks": [6, 7] },
    { "wave": 6, "tasks": [8] },
    { "wave": 7, "tasks": [9] }
  ]
}
```

## Tasks

### Task 1 — Domain entity
Add `ReadingStatusValue` enum and `ReadingStatus` dataclass to
`app/library/domain/entities.py`.

### Task 2 — Infrastructure
- Add `ReadingStatusModel` to `app/library/infrastructure/models.py`.
- Add `SqlReadingStatusRepository` to `app/library/infrastructure/repositories.py`.
- Create Alembic migration `0011_reading_status.py`.

### Task 3 — Protocol
Add `ReadingStatusRepository` protocol to
`app/library/application/protocols.py`.

### Task 4 — Use cases
- `app/library/application/set_reading_status.py` — upsert status.
- `app/library/application/get_reading_statuses.py` — list all for user.

### Task 5 — Endpoints
Add to `app/library/interface/books_router.py`:
- `PUT /books/{book_id}/status`
- `DELETE /books/{book_id}/status`
- `GET /books/statuses`

### Task 6 — Frontend types
Add `ReadingStatusValue`, `BookReadingStatus`, `BookWithStatus` to
`frontend/src/types/index.ts`.

### Task 7 — BookSpine component
Create `frontend/src/components/book-spine.tsx`.

### Task 8 — BookShelf component
Create `frontend/src/components/book-shelf.tsx`.

### Task 9 — Library page integration
Update `frontend/src/app/library/page.tsx`:
- Fetch statuses in parallel with books.
- Add view toggle (list ↔ shelf) with localStorage persistence.
- Render shelf view using `BookShelf`.
- Add status badge + change menu to list view rows.
