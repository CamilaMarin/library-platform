---
inclusion: always
---

# Compliance: Chile's Ley 21.719 (Data Protection Law)

References: `adr/0003-ley-21719-compliance.md`, `adr/0016-configurable-data-retention.md`

## Mandatory rules

- Any feature that creates, reads, modifies, or deletes personal data MUST log the operation in the audit log and in the `DataProcessingRecord` where applicable.
- Do not add any personal data field to the model without explicitly justifying its functional necessity (data minimization).
- The user's privacy panel MUST support all 4 ARCO rights (access, rectification, cancellation, opposition) plus portability, as self-service.
- No feature may share a user's data with another group member unless visibility has been explicitly configured by the data owner.
- Encrypt sensitive personal data and user digital files, both in transit and at rest.

## Retention policy (adr/0016)

- NEVER hardcode retention periods in source code.
- Retention durations MUST be configurable (database/config, adjustable without code changes).
- Retention policies MUST be documented and communicated to users.
- Users MUST be informed before any automated deletion triggered by retention expiry.

## Breach notification

- If a breach is detected, follow the documented playbook to notify APDP and affected users within 72 hours.
- Default to the widest reasonable notification scope when breach scope is unclear.

Full spec: `.kiro/specs/privacy/`
