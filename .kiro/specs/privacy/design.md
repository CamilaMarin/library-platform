# Design — Privacy & Ley 21.719 Compliance

Source: `docs/architecture/database.md`, `docs/domain/entities.md`.

### Referenced ADRs
- `adr/0003-ley-21719-compliance.md` — Ley 21.719 compliance from design
- `adr/0007-review-visibility-model.md` — Explicit visibility model
- `adr/0016-configurable-data-retention.md` — Configurable retention (no hardcoded periods)
- `adr/0017-cloud-agnostic-abstractions.md` — All infrastructure behind abstractions

## Overview

This module implements the cross-cutting privacy infrastructure required by Chile's Ley 21.719: consent tracking, a processing record, audit logging, self-service ARCO rights, configurable retention, and breach notification. Every other bounded context depends on the services defined here; it is not optional per-feature.

## Architecture

Implemented as a shared **infrastructure service** invoked from every bounded context's `application` layer:

```
interface/   → REST endpoints (privacy panel, export, deletion)
application/ → ExerciseARCORight use case; audit-log write calls embedded in every other context's use cases
domain/      → DataConsent, DataProcessingRecord, AuditLog, RetentionPolicy entities (framework-free)
infrastructure/ → Postgres, deletion job runner, encryption at rest, breach-notification playbook trigger
```

All infrastructure accessed via abstractions (adr/0017).

## Components and Interfaces

- **DataConsent**: user_id, timestamp, policy_version, purpose.
- **DataProcessingRecord**: user_id, data_type, purpose, legal_basis, collected_at, retention_expires_at.
- **AuditLog**: actor_user_id, action (create/read/update/delete), affected_entity, timestamp.
- **RetentionPolicy**: data_type, duration_days, description, active. Configurable — not hardcoded (adr/0016).

Use case: `ExerciseARCORight` (access, rectify, cancel, oppose, port).

Endpoints:
- `GET /users/me/export`
- `DELETE /users/me`
- `PATCH /users/me/privacy-settings`
- `GET /privacy/processing-record` (internal/audit)

## Data Models

```
DataConsent(id, user_id, timestamp, policy_version, purpose)
DataProcessingRecord(id, user_id, data_type, purpose, legal_basis, collected_at, retention_expires_at)
AuditLog(id, actor_user_id, action, affected_entity, timestamp)
RetentionPolicy(id, data_type, duration_days, description, active)
```

## Correctness Properties

- Every write to a personal-data field in any bounded context produces exactly one corresponding `AuditLog` entry in the same transaction.
- `DELETE /users/me` always results in: digital files purged from storage, AuditLog entries anonymized beyond minimum legal retention, and no residual DataConsent/DataProcessingRecord rows referencing a resolvable identity.
- No cross-user data read (reviews, reading history, etc.) is served unless the data owner's visibility setting explicitly permits it for that requester.
- `RetentionPolicy.duration_days` is read from configuration/database at runtime — never from a compile-time constant.
- Users are always notified before automated deletion triggered by retention expiry.

## Error Handling

- Cancellation requested while legally-required retention data still applies → data is anonymized rather than hard-deleted, user informed which fields are retained and why.
- Breach detection with unclear scope → default to widest reasonable notification scope; escalate to human review before 72h window closes.
- Export request on an account with very large associated data → asynchronous job with completion notification, not a blocking request.

## Testing Strategy

- Domain unit tests: audit-log-on-every-write invariant (via a test double context), retention-expiry calculation with configurable durations.
- Integration tests: full ARCO cycle (access → rectify → cancel) including verification that storage and logs are actually purged/anonymized.
- Cross-context test: pick one use case from each other bounded context (e.g. `CreateCopy`, `PostComment`) and assert it produces an AuditLog entry.
- Retention configuration test: verify changing RetentionPolicy.duration_days affects the deletion job without code changes.
- Playbook drill test (manual/documented, not automatable): simulate a breach and time the notification workflow against the 72h requirement.
