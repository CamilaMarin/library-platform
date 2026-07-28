# Requirements — Reading Status

## Introduction

Allows a user to assign a personal reading status to a book (not a copy).
The status represents the user's relationship with the intellectual work regardless
of how many physical or digital copies they own.

### Referenced ADRs
- `adr/0015-book-copy-separation.md` — Book/Copy separation (status belongs to Book, not Copy)
- `adr/0003-ley-21719-compliance.md` — Reading status is personal data

## Glossary

- **ReadingStatus**: a record linking a user to a book with one of four states.
  Key: `(user_id, book_id)`. Unique per pair.
- **Status values**: `want_to_read` · `reading` · `read` · `dnf` (did not finish)
- **Shelf view**: library display mode that groups books into horizontal shelves by status,
  each book rendered as a vertical spine.
- **List view**: current library display mode (flat list of cards).

## Requirements

### Requirement 1: Set reading status

**User Story:** As a reader, I want to mark a book as "want to read", "reading",
"read", or "did not finish", so I can track my reading journey.

#### Acceptance Criteria
1. THE SYSTEM SHALL allow setting a status for any book in the user's library via
   `PUT /books/{book_id}/status`.
2. THE SYSTEM SHALL accept exactly one of: `want_to_read`, `reading`, `read`, `dnf`.
3. IF a status already exists for that `(user_id, book_id)` pair, THE SYSTEM SHALL
   update it (upsert — not create a duplicate).
4. THE SYSTEM SHALL allow removing a status (`DELETE /books/{book_id}/status`),
   returning the book to "no status" state.
5. Only the authenticated user can set or delete their own status — no cross-user access.

### Requirement 2: Retrieve statuses

**User Story:** As a reader, I want to see all my books with their reading status
at once, so I can see my shelf view.

#### Acceptance Criteria
1. THE SYSTEM SHALL expose `GET /books/statuses` returning all `(book_id, status)`
   pairs for the authenticated user in a single request.
2. Books with no status assigned SHALL NOT appear in this response (they are
   "unclassified" and rendered separately in the shelf view).

### Requirement 3: Shelf view (frontend)

**User Story:** As a reader, I want to see my library as a bookshelf with spines
grouped by reading status, so the library feels like a physical space.

#### Acceptance Criteria
1. THE SYSTEM SHALL provide a toggle on the library page to switch between
   list view and shelf view.
2. In shelf view, books SHALL be grouped into labeled shelves:
   "Leyendo ahora" · "Quiero leer" · "Leídos" · "No terminados".
3. A shelf for "Sin clasificar" SHALL appear at the end for books with no status.
4. Each book SHALL be rendered as a vertical spine (title rotated, color derived
   from the status palette).
5. Clicking a spine SHALL open a popover/menu allowing the user to change or
   remove the status without leaving the shelf view.
6. The toggle preference SHOULD be persisted in localStorage so it survives
   page refresh.
7. The shelf view SHALL be accessible: each spine has an accessible label and
   the status menu is keyboard-navigable.
