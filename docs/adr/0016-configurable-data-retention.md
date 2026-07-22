# ADR-0016: Configurable Data Retention

## Status
Accepted

## Context
Ley 21.719 (Chile's Data Protection Law) requires data retention policies but does not prescribe specific periods for all cases. Hardcoding retention periods makes it difficult to adapt to regulatory changes or future legal interpretations.

## Decision
- **Do not hardcode retention periods** in source code.
- Retention policies must be **configurable** (via application configuration, not code constants).
- Every policy must be **documented** and understandable to the user.
- Users must be **informed before any deletion** triggered by retention expiry.

## Consequences
- A `RetentionPolicy` table or configuration is needed that defines periods per data type.
- The account cancellation flow does not purge immediately — it informs the user of the timeline and then executes the purge according to the configured policy.
- Makes it easier to adapt if APDP issues specific guidance on retention periods.
- Requires a periodic job that evaluates expired data against the active policy.
