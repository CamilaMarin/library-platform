# Changelog — EntreLíneas

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
