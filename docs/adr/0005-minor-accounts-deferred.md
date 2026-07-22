# ADR-0005: Minor Accounts Deferred to v2

## Status
Accepted

## Context
Business rule 5 requires that every minor's account be managed by a responsible adult in the same family group. This introduces significant complexity in the MVP permission model (differentiated permissions, parental approval, content restrictions).

## Decision
- Minor accounts are postponed to version 2.
- In the MVP, all users share the same permission model — no adult/minor distinction.

## Consequences
- Simplifies registration flow and family group management in the MVP.
- Business rule 5 (`domain/business-rules.md`) remains valid but its implementation is deferred.
- `date_of_birth` is not required as a mandatory field in MVP registration (though it can be optionally captured).
- Before v2, the differentiated permission model and minor-adult linking must be designed.
