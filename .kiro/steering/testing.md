---
inclusion: always
---

# Testing Rules — EntreLíneas

## General

- Every new feature requires tests (domain + integration) before being considered done.
- Prefer testing the domain layer without mocking infrastructure (Clean Architecture makes this natural).
- Prioritize clarity in test names — they serve as documentation.

## Correctness properties

- Every correctness property defined in a design spec (`### Property N:`) MUST have at least one corresponding test.
- These tests validate the formal invariants of the system — they are not optional.

## Required test types per module

- **Domain unit tests:** business rules, invariants, state machines — no DB, no HTTP.
- **Integration tests:** happy paths through endpoints, error responses, persistence.
- **Security tests:** ownership validation, access control, no information leakage.
- **Cross-context tests:** verify bounded contexts don't leak internal data to each other (e.g., `file_ref` never crosses from Library to Community).

## Testing framework

- Backend: Pytest
- Focus on the domain layer (pure functions, no mocks needed thanks to Clean Architecture)
- Integration tests for critical endpoints (auth, file access, ARCO, loans)

## Do not add libraries without justification

Rule 7 of architecture applies to test libraries too — use Pytest and its ecosystem before reaching for alternatives.
