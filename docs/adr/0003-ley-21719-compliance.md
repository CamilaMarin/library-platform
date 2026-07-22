# ADR-0003: Ley 21.719 (Chile's Data Protection Law) Compliance from Design

## Status
Accepted

## Context
Ley 21.719 (Chile's Data Protection Law) enters full effect on December 1, 2026, aligned with GDPR standards: it creates the Data Protection Agency (APDP), mandates ARCO rights + portability, requires breach notification within 72 hours, and fines up to 20,000 UTM or 4% of annual revenue for repeat offenses. It applies to any organization processing data of individuals in Chile, regardless of size.

## Decision
- Privacy by Design from the first sprint, not as a post-MVP adjustment.
- Every entity storing personal data is linked to a processing record (`DataProcessingRecord`) and to audit logs.
- The user's privacy panel (`/privacy`) implements all 4 ARCO rights + portability as self-service, without going through support.
- A documented breach notification playbook within 72 hours exists.
- Data minimization: no field is added to the model without justifying its explicit functional necessity (e.g., national ID is never requested).

## Consequences
- Higher design and development overhead than a typical MVP, but avoids redesigning the data model under pressure before December 2026.
- Serves as a portfolio differentiator: few personal projects document real regulatory compliance from the ADR level.
- Requires external legal review before any launch with real data (outside the scope of this document, which is general guidance and not legal advice).
