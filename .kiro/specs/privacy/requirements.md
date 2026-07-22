# Requirements Document

## Introduction

This module implements the cross-cutting privacy infrastructure required by Chile's Ley 21.719: consent tracking, a processing record, audit logging, self-service ARCO rights, configurable retention, and breach notification. Every other bounded context depends on the services defined here.

Source: `docs/domain/business-rules.md` (rules 4, 7, 10, 11), `adr/0003-ley-21719-compliance.md`.

### Referenced ADRs
- `adr/0003-ley-21719-compliance.md` — Ley 21.719 compliance from design
- `adr/0007-review-visibility-model.md` — Explicit visibility model (shared_with)
- `adr/0016-configurable-data-retention.md` — Configurable retention (no hardcoded periods)
- `adr/0017-cloud-agnostic-abstractions.md` — All infrastructure behind abstractions

## Glossary

- **ARCO**: Access, Rectification, Cancellation, Opposition rights, plus portability.
- **APDP**: Chile's Data Protection Agency, the enforcement body under Ley 21.719.
- **DataProcessingRecord**: log of what personal data is processed, why, and for how long it is retained.

## Requirements

### Requirement 1: Ley 21.719 compliance

**User Story:** As a user, I want certainty that my personal data and my family's are handled securely and transparently, so I can trust the platform.

#### Acceptance Criteria
1. THE SYSTEM SHALL maintain an auditable record of data processing activities (what data, purpose, retention period).
2. THE SYSTEM SHALL implement all 4 ARCO rights (access, rectification, cancellation, opposition) plus portability, executable by the user with no friction.
3. IF a security breach affecting personal data occurs, THEN THE SYSTEM SHALL follow a documented procedure to notify Chile's Data Protection Agency (APDP) and affected data subjects within 72 hours.
4. THE SYSTEM SHALL apply data minimization: never request or store any personal data field that is not strictly necessary for the offered functionality.
5. THE SYSTEM SHALL maintain audit logs of who accessed, modified, or deleted personal data, and when.
6. THE SYSTEM SHALL encrypt sensitive personal data and users' digital files, both in transit and at rest.
7. THE SYSTEM SHALL define and apply a configurable data retention policy (never hardcoded in source code), documented and communicated to users. Users SHALL be informed before any automated deletion. Retention duration must be adjustable without code changes.
8. BEFORE sharing any user's data with another group member, THE SYSTEM SHALL require that visibility level to have been explicitly configured by the data's owner.

> Reference: `adr/0016-configurable-data-retention.md` — Retention periods must be configurable, not hardcoded.
> Reference: `adr/0003-ley-21719-compliance.md` — Privacy by Design from Sprint 1.
