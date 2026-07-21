# Requirements Document

## Introduction

This module covers account registration with explicit data-processing consent, JWT-based authentication (access + refresh tokens), and family group creation/invitation. It is the foundation every other bounded context depends on for `user_id` and `group_id`.

ARCO rights (access, rectification, cancellation, opposition, portability) are owned by the Privacy module and integrated here via cross-cutting calls.

Source: `docs/specs/authentication.md`, `docs/domain/business-rules.md` (rules 4, 5).

### Referenced ADRs
- `adr/0004-custom-jwt-authentication.md` — JWT Access + Refresh Tokens
- `adr/0005-minor-accounts-deferred.md` — Minor accounts deferred to v2
- `adr/0017-cloud-agnostic-abstractions.md` — All infrastructure behind abstractions

## Glossary

- **User**: person with an account, always the owner of their own data.
- **FamilyGroup**: set of users who have invited and accepted each other.
- **DataConsent**: record of a user's explicit consent to data processing.
- **Access Token**: short-lived JWT used to authenticate API requests.
- **Refresh Token**: long-lived token used to obtain new Access Tokens without re-login.

## Requirements

### Requirement 1: Registration and consent

**User Story:** As a new user, I want to create my account and understand what happens with my data, so I can confidently decide whether to use the platform.

#### Acceptance Criteria
1. WHEN a user creates an account, THE SYSTEM SHALL request explicit, informed consent (purpose + legal basis) before enabling any functionality.
2. THE SYSTEM SHALL record a timestamp and accepted policy version in `DataConsent`.
3. THE SYSTEM SHALL store passwords with a secure hashing algorithm (bcrypt or argon2), never in plain text.

### Requirement 2: JWT Authentication

**User Story:** As a registered user, I want to log in securely and maintain my session active without constantly re-authenticating.

#### Acceptance Criteria
1. WHEN login is successful, THE SYSTEM SHALL issue an Access Token (short-lived JWT) and a Refresh Token (long-lived).
2. THE SYSTEM SHALL validate the Access Token on every authenticated request without consulting server-side state.
3. THE SYSTEM SHALL allow rotating the Refresh Token (issuing a new one and invalidating the previous) via `POST /auth/refresh`.
4. THE SYSTEM SHALL allow revoking a Refresh Token (logout) via `POST /auth/logout`.
5. THE SYSTEM SHALL reject expired or revoked tokens with `401 Unauthorized`.

> Reference: `adr/0004-custom-jwt-authentication.md`

### Requirement 3: Family group

**User Story:** As a user, I want to create or join a family group, so I can share the reading experience with the right people.

#### Acceptance Criteria
1. THE SYSTEM SHALL allow creating a family group and inviting other profiles.
2. An invited profile SHALL NEVER join the group without explicitly accepting the invitation.

> Note: Minor account management (adult responsible) is deferred to v2 per `adr/0005-minor-accounts-deferred.md`. All MVP users share the same permission model.

### Requirement 4: Account and personal data

**User Story:** As a user, I want full control over my account data, so I can exercise my privacy rights without friction.

#### Acceptance Criteria
1. THE SYSTEM SHALL allow exporting or deleting the account and all associated data from the user's own profile, without support intervention.
2. THE SYSTEM SHALL integrate with the Privacy module's `ExerciseARCORight` implementation for export and cancellation flows.
