# Database — EntreLíneas

PostgreSQL. See also `domain/entities.md` for the DDD view of the same model.

## MVP Tables

### Identity & Privacy
- **users**(id, name, email, password_hash, date_of_birth[optional], privacy_settings, created_at)
- **data_consents**(id, user_id, timestamp, policy_version, purpose)
- **refresh_tokens**(id, user_id, token_hash, expires_at, revoked, created_at)
- **family_groups**(id, name, created_at)
- **group_memberships**(group_id, user_id, status[invited|accepted])

### Library
- **books**(id, title, author, genres[], description, pages, isbn)
- **copies**(id, user_id, book_id, type[physical|digital], file_ref, status[available|on_loan])
- **reading_progress**(id, user_id, copy_id, position, percentage, last_read_at)
- **bookmarks**(id, user_id, copy_id, position, label, created_at)
- **notes**(id, user_id, copy_id, position, text, created_at, updated_at)

### Community
- **clubs**(id, group_id, name, active_book_id, discussion_date)
- **reading_turns**(id, club_id, book_id, current_user_id)
- **turn_comments**(id, turn_id, user_id, text, is_spoiler)

### Circulation
- **loans**(id, copy_id, borrower_user_id, loan_date, estimated_return_date, status)

### Reviews
- **reviews**(id, user_id, book_id, rating, text, visibility[private|shared], shared_with_type[group|club|null], shared_with_id[nullable])

### Privacy & Audit
- **data_processing_records**(id, user_id, data_type, purpose, legal_basis, collected_at, retention_expires_at)
- **audit_logs**(id, actor_user_id, action, affected_entity, timestamp)
- **retention_policies**(id, data_type, duration_days, description, active)

### Reading Selection
- **draws**(id, group_id, filters_json, result_book_id, result_source_user_id, timestamp)

## Application-Level Constraints (not DB-only)

- `copies.file_ref` is only resolved for requests where `request.user_id == copies.user_id`.
- `loans.copy_id` must reference a copy with `type = 'physical'` (validated in the use case, reinforced with a check constraint if the engine supports it).
- `reviews.shared_with_id` can only be NOT NULL when `visibility = 'shared'`.
- `reading_progress`, `bookmarks`, and `notes` can only exist for digital copies whose `user_id` matches the record's user_id.

## Changes from Previous Design

- Removed `role[adult|minor]` from `group_memberships` — minor accounts deferred to v2 (see `adr/0005`).
- Added `refresh_tokens` — custom JWT with rotation (see `adr/0004`).
- Changed review visibility to `visibility` + `shared_with_type` + `shared_with_id` model (see `adr/0007`).
- Added reader tables: `reading_progress`, `bookmarks`, `notes` (see `adr/0014`).
- Added `retention_policies` — configurable periods, not hardcoded (see `adr/0016`).
- Added `draws` — reading selection as a dedicated feature (see `adr/0013`).
- All table names now use English snake_case.

## v2 Tables (enriched catalog, not MVP)

- **authors**, **series**, **publishers**, **collections** — normalization of metadata currently embedded as free text in `books`.
- Fields/tables for minor account management (see `adr/0005`).

## Suggested Indexes

- `copies(user_id)`, `copies(book_id)` — personal library and draw queries.
- `audit_logs(actor_user_id, timestamp)` — audit queries by date range.
- `refresh_tokens(token_hash)` — fast refresh token validation.
- `reading_progress(user_id, copy_id)` — progress lookup when opening the reader.
