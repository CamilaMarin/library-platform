# Domain Entities — EntreLíneas (DDD)

## Bounded Contexts

### 1. Identity & Privacy
- **User** (aggregate root): id, name, email, password_hash, privacy_settings.
- **DataConsent** (value object / internal entity): timestamp, policy_version, purpose.
- **RefreshToken** (entity): token, user_id, expires_at, revoked.

> Note: `date_of_birth` is optional in the MVP. Minor accounts deferred to v2 (see `adr/0005-minor-accounts-deferred.md`).

### 2. Library
- **Book** (catalog entity): title, author, genres, description, pages, ISBN. Represents the intellectual work. Can exist without anyone owning a copy.
- **Copy** (aggregate root, belongs to a User): type (physical/digital), file_ref (digital only, never exposed outside owner), status. Each copy has exactly one owner.
- **ReadingProgress** (entity within Copy aggregate): user_id, copy_id, position, percentage, last_read_at.
- **Bookmark** (entity): user_id, copy_id, position, label.
- **Note** (entity): user_id, copy_id, position, text.

### 3. Community
- **FamilyGroup** (aggregate root): members with status (invited/accepted).
- **Club** (aggregate root): associated group (single group in MVP), active_book, discussion_date.
- **ReadingTurn** (entity within Club aggregate): current_user, comments.

> Note: In the MVP, clubs only exist within a family group. "Connected groups" removed from MVP (see `adr/0006-no-connected-groups-mvp.md`).

### 4. Circulation
- **Loan** (aggregate root): references a Copy of type physical exclusively, borrower, dates, status.

### 5. Reviews
- **Review** (aggregate root): user, book, rating (integer 1–5), text, visibility (`private` | `shared`), shared_with_type, shared_with_id.

> Note: Visibility uses the `visibility` + `shared_with` explicit model, not the old `private|group|club` (see `adr/0007-review-visibility-model.md`).

### 6. Reading Selection
- **Draw** (entity): group_id, applied filters, result, timestamp.
- Availability logic validates that each participant has authorized access to the book (see `adr/0008-reading-selection-availability.md`).

## Aggregate Invariants (summary — detail in business-rules.md)

- A digital Copy can only have one owner `user_id`, immutable after creation.
- A Loan can only be created referencing a Copy with `type = physical`.
- A ReadingTurn cannot be activated for a user who doesn't own their own Copy of the Book in question.
- The integrated reader can only open a file whose `copy.user_id == request.user_id`.

## Relationship Between Contexts

Contexts share identifiers (`user_id`, `book_id`) but not internal models — for example, "Community" doesn't know the `file_ref` of a Copy, it only knows one exists and who owns it.
