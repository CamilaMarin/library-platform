# Design — Authentication & Groups

Source: `docs/architecture/architecture.md`, `docs/architecture/database.md`, `docs/domain/entities.md`.

### Referenced ADRs
- `adr/0004-custom-jwt-authentication.md` — JWT Access + Refresh Tokens
- `adr/0005-minor-accounts-deferred.md` — Minor accounts deferred to v2
- `adr/0017-cloud-agnostic-abstractions.md` — All infrastructure behind abstractions

## Overview

This module covers user registration with explicit data-processing consent, JWT-based authentication (access + refresh tokens), and family group creation/invitation. It is the foundation every other bounded context depends on for `user_id` and `group_id`.

ARCO rights execution is owned by the Privacy module; this module integrates via cross-cutting calls.

## Architecture

Clean Architecture, bounded context **Identity & Privacy**:

```
interface/   → REST endpoints (auth, users, groups)
application/ → use cases (see Components below)
domain/      → User, DataConsent, FamilyGroup entities; no framework/DB imports
infrastructure/ → Postgres repositories, password hashing (bcrypt/argon2), JWT token service
```

All infrastructure dependencies accessed via abstractions (adr/0017).

## Components and Interfaces

- **User** (aggregate root): id, name, email, password_hash, privacy_settings.
- **DataConsent**: timestamp, policy_version, purpose, legal_basis.
- **RefreshToken**: id, user_id, token_hash, expires_at, revoked, created_at.
- **FamilyGroup** (aggregate root): members[] with status (invited | accepted).

Use cases: `RegisterUser`, `LoginUser`, `RefreshToken`, `RevokeToken`, `CreateFamilyGroup`, `InviteGroupMember`, `AcceptGroupInvitation`.

Endpoints:
- `POST /auth/register`, `POST /auth/consent`
- `POST /auth/login` → returns Access Token + Refresh Token
- `POST /auth/refresh` → rotates Refresh Token, issues new Access Token
- `POST /auth/logout` → revokes Refresh Token
- `GET/PATCH/DELETE /users/me`, `GET /users/me/export`
- `POST /groups`, `POST /groups/{id}/invitations`, `POST /groups/{id}/invitations/{id}/accept`

## Data Models

```
User(id, name, email, password_hash, privacy_settings, created_at)
DataConsent(id, user_id, timestamp, policy_version, purpose, legal_basis)
RefreshToken(id, user_id, token_hash, expires_at, revoked, created_at)
FamilyGroup(id, name, created_at)
GroupMembership(group_id, user_id, status[invited|accepted])
```

> Note: No `role[adult|minor]` in MVP — minor accounts deferred to v2 (adr/0005).

## Correctness Properties

### Property 1: Consent-gating
A `User` row is never created without a corresponding `DataConsent` row in the same transaction.
**Validates: Requirements 1.1**

### Property 2: Invitation state machine
A `GroupMembership.status` can only transition `invited → accepted` via an explicit action by the invited `user_id`; no other path exists.
**Validates: Requirements 3.2**

### Property 3: Stateless token validation
A valid Access Token contains `user_id` and `exp`; validation never requires a database lookup.
**Validates: Requirements 2.2**

### Property 4: Refresh token rotation atomicity
Refresh Token rotation always invalidates the previous token in the same transaction as issuing the new one (prevents replay).
**Validates: Requirements 2.3**

### Property 5: Revocation enforcement
A revoked Refresh Token can never be used to obtain a new Access Token.
**Validates: Requirements 2.4**

## Error Handling

- Registration without consent acceptance → reject with `400 consent_required`, no partial `User` record persisted.
- Invitation acceptance by a user who is not the invitee → `403 forbidden`.
- Login with invalid credentials → generic `401 invalid_credentials` (no user-enumeration hints).
- Expired Access Token → `401 token_expired`.
- Revoked or expired Refresh Token on `/auth/refresh` → `401 token_revoked`.
- ARCO cancellation → delegated to Privacy module's deletion flow.

## Testing Strategy

- Domain unit tests: consent-gating invariant, invitation state machine — no DB or HTTP involved.
- Integration tests: register → consent → login → receive tokens; refresh → rotate; logout → revoke; invite → accept happy path.
- Security tests: no user-enumeration via login/registration error messages; expired/revoked tokens correctly rejected; refresh token replay after rotation is rejected.
