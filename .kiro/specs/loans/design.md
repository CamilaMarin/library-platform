# Design — Loans

Source: `docs/architecture/database.md`, `docs/domain/entities.md`.

### Referenced ADRs
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation
- `adr/0015-book-copy-separation.md` — Loans reference Copies (not Books)

## Overview

This module records physical-book loans between people. It is deliberately narrow: loans exist only for physical copies. Digital "lending" is out of scope by design — see `clubs` spec's ReadingTurn for the digital equivalent.

## Architecture

Clean Architecture, bounded context **Circulation**:

```
interface/   → REST endpoints (loans)
application/ → use cases (RegisterLoan, RegisterReturn)
domain/      → Loan entity; enforces physical-only invariant
infrastructure/ → Postgres
```

## Components and Interfaces

- **Loan** (aggregate root): copy_id (must reference a Copy of type `physical`), borrower_user_id, loan_date, estimated_return_date, status.

Endpoints:
- `POST /copies/{id}/loans`
- `PATCH /loans/{id}/return`

## Data Models

```
Loan(id, copy_id, borrower_user_id, loan_date, estimated_return_date, status[active|returned])
```

## Correctness Properties

- `Loan.copy_id` always references a `Copy` with `type == physical`; enforced at the application layer before persistence.
- A `Copy` cannot have two simultaneous `active` loans.
- Loan creation always flips the referenced `Copy.status` to `on_loan` in the same transaction.
- Loan return always flips the referenced `Copy.status` back to `available` in the same transaction.

## Error Handling

- Attempt to create a loan for a digital copy → `422 invalid_copy_type`, no Loan row created.
- Attempt to loan a copy already `on_loan` → `409 conflict`.
- Return of a loan already marked `returned` → idempotent `200`, no duplicate state change.

## Testing Strategy

- Domain unit test: loan creation rejected for `type == digital`.
- Integration tests: full loan → return cycle; double-loan rejection; idempotent return; Copy.status transitions.
- Regression test tied to ADR-0001: assert no endpoint in this module ever accepts or returns a `file_ref`.
