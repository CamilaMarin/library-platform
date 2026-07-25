# Changelog — EntreLíneas

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [M6] — Reviews

### Added
- Review domain entity with explicit visibility control (private | shared + shared_with target)
- Visibility enum (PRIVATE, SHARED) and SharedWithType enum (GROUP, CLUB)
- Visibility invariants enforced in entity constructor (ADR-0007)
- CreateReview use case + POST /reviews endpoint (explicit visibility required, Req 1.5)
- EditReview use case + PATCH /reviews/{id} (author-only, partial updates, visibility invariants preserved)
- DeleteReview use case + DELETE /reviews/{id} (author-only, 204 No Content)
- ListReviews use case + GET /books/{id}/reviews (access-controlled: own + shared-with-membership)
- MembershipChecker protocol + SqlMembershipChecker (queries group_memberships + clubs tables)
- ExportReviews use case (ARCO access right — all user reviews for data export)
- DeleteUserReviews use case (ARCO cancellation right — hard-delete all user reviews)
- ReviewRepository protocol with find_by_id, find_by_book_id, find_by_user_id, save, update, delete, delete_all_by_user_id
- SqlReviewRepository (SQLAlchemy implementation)
- ReviewModel (SQLAlchemy ORM) + books_reviews_router for GET /books/{id}/reviews
- 85 tests (domain + use case + integration + comprehensive access control + privacy)

### Security
- No review is ever served without an explicit access check (Property 5)
- Private reviews only visible to author (Property 4)
- Shared reviews only visible to active members of the target group/club at query time (Property 3)
- Membership changes take effect immediately — no cached access (dynamic at query time)
- Non-author edit/delete returns 403 Forbidden
- Reviews are personal data (ADR-0003): included in ARCO export, deleted on account cancellation

## [M5] — Clubs & Reading Turns

### Added
- Club domain entity (group_id singular per ADR-0006, name required)
- ReadingTurn entity (coordinates who reads, validates copy ownership)
- Comment entity (is_spoiler defaults to false per Property 3)
- CreateClub use case + endpoint
- SetActiveBook use case + endpoint
- PostComment use case + endpoint
- ActivateReadingTurn use case (validates copy ownership — Property 1)
- CopyOwnershipQuery protocol (cross-context read, never file_ref)
- Alembic migration 0007: clubs, reading_turns, turn_comments tables
- 17 tests (8 domain + 9 integration)

### Security
- ActivateReadingTurn rejects users without a copy (CopyOwnershipError → 409)
- CopyOwnershipQuery never returns file_ref (cross-context isolation)

### Fixed
- conftest.py teardown: use CASCADE for table drops with foreign keys

## [M4] — Reading Selection

### Added
- Draw domain entity (group_id, filters, participants, result)
- TurnHistory domain entity (fair rotation tracking)
- Availability validation logic (physical: available status, digital: ownership)
- RunReadingDraw use case (filter by genre/pages/unread, validate availability, random select)
- PickByTurn use case (deterministic rotation: oldest last_pick_date goes next)
- POST /groups/{id}/draws — execute filtered random draw
- GET /groups/{id}/draws — draw history
- GET /groups/{id}/draws/next-picker — who picks next
- SqlDrawRepository, SqlTurnHistoryRepository, SqlCopyQueryService, SqlBookQueryService
- Alembic migration 0006: draws, turn_histories tables
- 21 tests (11 domain + 10 integration) covering all correctness properties

### Security
- CopyQueryService uses `[redacted]` placeholder for digital file_ref (never exposes actual path)
- Draw results never include file_ref (Property 3)
- Source user attribution does not imply file access (Property 4)

## [M3] — Library

### Added
- Book domain entity (title, author, genres, description, pages, ISBN)
- Copy domain entity (physical/digital, per-user ownership, file isolation)
- CreateBook use case + POST /books endpoint
- CreateCopy use case + POST /copies/physical, POST /copies/digital endpoints
- EditBook use case + PATCH /books/{id}
- DeleteBook use case + DELETE /books/{id} (409 if copies exist)
- DeleteCopy use case + DELETE /copies/{id} (owner-only, removes file if digital)
- SearchBooks use case + GET /books?query= (personal + group library, metadata only)
- FileStorage protocol + LocalFileStorage adapter (per-user isolation)
- BookRepository and CopyRepository protocols + SQL implementations
- Alembic migration 0005: books, copies tables
- 26 tests (11 domain + 15 integration) covering all correctness properties

### Security
- CopyResponse NEVER exposes file_ref (ADR-0009 Property 2)
- DeleteCopy validates ownership before deletion (403 for non-owners)
- Search results never include file_ref from other users' copies (Property 5)

### Added (M1 — Authentication, in progress)
- User domain entity with email/name validation and bcrypt password hash storage
- RefreshToken domain entity with is_expired/is_usable properties and timezone-safe comparison
- RegisterUser use case with consent-gating invariant (User + DataConsent in same transaction)
- LoginUser use case with bcrypt verification, JWT Access + Refresh Token issuance, SHA-256 refresh token storage
- RefreshTokenUseCase with atomic rotation (revoke old + store new in same transaction)
- UserRepository and RefreshTokenRepository protocols (application layer abstractions)
- SqlUserRepository and SqlRefreshTokenRepository (SQLAlchemy implementations)
- UserModel and RefreshTokenModel (SQLAlchemy ORM)
- REST endpoints: POST /auth/register, /auth/consent, /auth/login, /auth/refresh
- Pydantic request/response schemas (RegisterRequest, LoginRequest, RefreshRequest, etc.)
- Alembic migration 0003: users and refresh_tokens tables
- RevokeTokenUseCase (logout) — always returns 200 to prevent info leakage
- POST /auth/logout endpoint with security-first design (no info leakage on invalid tokens)
- FamilyGroup and GroupMembership domain entities with MembershipStatus enum
- CreateFamilyGroup use case (creator auto-added as accepted member)
- POST /groups/ endpoint with JWT authentication requirement
- get_current_user_id dependency (extracts user from Bearer token — reusable for all auth endpoints)
- FamilyGroupRepository and GroupMembershipRepository protocols + SQL implementations
- FamilyGroupModel and GroupMembershipModel (SQLAlchemy ORM)
- Alembic migration 0004: family_groups and group_memberships tables
- 90 tests (domain unit + endpoint integration) — all passing
- ExportUserData use case — collects all identity-owned data (ARCO access right)
- DeleteUserAccount use case — permanent deletion with token revocation (ARCO cancellation right)
- GET /users/me/export endpoint with structured JSON export (no password_hash exposed)
- DELETE /users/me endpoint for self-service account deletion
- Users router with JWT authentication dependency
- Added repository methods: find_all_by_user_id, delete, delete_by_user_id, revoke_all_by_user_id
- Comprehensive acceptance test suite (28 tests) covering all requirements and correctness properties
- 154 tests total (domain unit + endpoint integration + security + acceptance)

## [M0] — Privacy Foundation

### Added
- DataConsent domain entity with validation (requires policy_version + purpose)
- DataProcessingRecord domain entity
- AuditLog domain entity + AuditService (high-value operations: registration, login, deletion, file upload, ARCO)
- RetentionPolicy domain entity (configurable duration, no automated job)
- Repository protocols (DataConsentRepository, DataProcessingRecordRepository, AuditLogRepository, RetentionPolicyRepository)
- SQLAlchemy ORM models for all 4 privacy tables
- SQLAlchemy repository implementations
- Alembic migration 0002: data_consents, data_processing_records, audit_logs, retention_policies tables
- 10 domain unit tests (entities + AuditService with in-memory test double)

## [M-1] — Architecture Validation

### Added
- Docker Compose with PostgreSQL 16 and MinIO (S3-compatible local storage)
- FastAPI backend skeleton with SQLAlchemy and Alembic
- `GET /health` endpoint with database connectivity check
- JWT utility proof-of-concept (PyJWT: create, verify, expiry, tamper detection)
- Next.js + TypeScript + Tailwind frontend skeleton
- Frontend /health call displaying backend status
- CORS middleware for local development
- GitHub Actions CI workflow (Ruff lint + Pytest)
- .env-based configuration (DATABASE_URL)
- Makefile with `up`, `down`, `test`, `lint` shortcuts

### Validated
- Full stack e2e: Docker → PostgreSQL → FastAPI → Next.js
- JWT issuance and verification works with PyJWT
- Alembic migrations run against Docker PostgreSQL
- 4 tests passing, lint clean
