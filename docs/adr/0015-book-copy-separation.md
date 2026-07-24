# ADR-0015: Book / Book Copy Separation

## Status
Accepted

## Context
The domain model already distinguished between Book (work metadata) and Copy (instance owned by a user). This ADR formalizes and reinforces that separation as an explicit architectural decision.

## Decision
Maintain strict separation between:

- **Book:** Represents the intellectual work. Contains shareable metadata (title, author, genres, description, pages, ISBN). Can exist without anyone owning a copy.
- **Book Copy:** Represents an owned instance. Each copy has exactly one owner (`user_id`). Can be physical (metadata + status only) or digital (encrypted, isolated file).

Relationship: A Book can have multiple Copies. Each Copy belongs to exactly one User.

## Consequences
- This model naturally supports: physical books, digital books, loans (on physical copies), shared libraries (Book metadata visible to the group, Copies as ownership detail).
- Loans reference a Copy, not a Book.
- The draw algorithm crosses Books × Copies × participants to determine availability.
- Deleting a Book is only possible if it has no associated Copies (or the requesting user's own copies are cascade-deleted). Current decision: reject with `409 conflict`.
