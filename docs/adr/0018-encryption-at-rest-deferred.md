# ADR-0018: Application-Level Encryption at Rest Deferred to Post-MVP

## Status
Accepted

## Context
Requirement 1.6 of the privacy spec states: "THE SYSTEM SHALL encrypt sensitive personal data and users' digital files, both in transit and at rest." ADR-0003 commits to Privacy by Design from the first sprint.

During implementation of the Privacy Panel milestone (M8), the team determined that application-level encryption at rest (field-level encryption, encrypted file storage beyond provider defaults) adds significant complexity to the MVP without proportional risk reduction at this stage:

- The platform will not process real user data until after external legal review (Task 10, a hard gate).
- In-transit encryption (TLS) remains fully enforced.
- The hosting provider's infrastructure-level encryption (disk encryption, database encryption at the storage layer) provides a baseline that satisfies the spirit of the requirement for a pre-launch portfolio project.
- Application-level encryption at rest introduces key management complexity, complicates querying/indexing, and increases development time for the MVP.

## Decision
Defer application-level encryption at rest to a post-MVP milestone. Task 6 in the privacy spec is marked as skipped (`[-]`) for the current release.

Before any launch with real user data:
1. Evaluate whether infrastructure-level encryption (cloud disk encryption, PostgreSQL TDE) is sufficient under Ley 21.719's "appropriate technical measures" standard.
2. If not, implement field-level encryption for identified sensitive fields (e.g., email, names) and encrypted blob storage for digital files.
3. This evaluation is gated by Task 10 (external legal review).

## Consequences
- Reduces M8 scope and unblocks the Release Candidate milestone (M9).
- Encryption in transit (TLS everywhere) remains non-negotiable and is already enforced.
- No real user data will be processed without completing the legal review gate, which will reassess this decision.
- Risk accepted: if the legal review determines field-level encryption is required, retrofitting it will require a migration (schema changes, re-encryption of existing data). This cost is accepted as low while the platform has no real users.
- Must be revisited before December 2026 (Ley 21.719 full enforcement date).

## Alternatives Considered
1. **Implement now**: Full field-level encryption + encrypted file storage. Rejected due to key management complexity and limited benefit before real users exist.
2. **Infrastructure-only (permanent)**: Rely solely on provider-level encryption forever. Rejected as a permanent decision — legal review may require more.
3. **Encrypt only digital files, not DB fields**: Partial approach. Rejected for now as it still requires key management infrastructure without covering the full requirement.

## Related
- ADR-0003: Ley 21.719 compliance from design
- ADR-0017: Cloud-agnostic abstractions (encryption provider would follow this pattern)
- Spec: `.kiro/specs/privacy/` — Requirement 1.6, Task 6
- Milestone: M8 (Privacy Panel)
