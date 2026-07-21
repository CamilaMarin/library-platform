---
inclusion: always
---

# MVP Domain Constraints — EntreLíneas

## Active MVP scope

- Authentication: JWT custom only (Access + Refresh Token). See `adr/0004`.
- Library: Book/Copy separation (adr/0015). Integrated EPUB/PDF reader (adr/0014). Search and Import are use cases within Library (adr/0010, adr/0011).
- Clubs: only within a single family group. No "connected groups" in MVP (adr/0006).
- Loans: physical copies only. No digital lending.
- Reviews: visibility `private | shared` with explicit `shared_with` target (adr/0007). Rating 1–5 integer.
- Reading Selection: random draw with availability rule (adr/0008) + pick-by-turn. Dedicated spec (adr/0013).
- Privacy: Ley 21.719 from day one. Configurable retention (adr/0016).

## Excluded from MVP (do not implement)

- Minor accounts / adult-minor linking (deferred to v2, adr/0005).
- Connected groups / multi-group clubs (eliminated from MVP, adr/0006).
- Redis (eliminated from MVP, adr/0012).
- Public feeds, social discovery, or any public-facing content.
- File sharing between accounts under any concept.

## Key domain invariants

- A digital `Copy.file_ref` is NEVER exposed to a non-owner.
- A `Loan` can only reference a `Copy` with `type == physical`.
- A `ReadingTurn` requires the user to own their own copy.
- No personal data is processed without valid `DataConsent`.
- No group membership without explicit invitation acceptance.
- `DeleteBook` returns `409 conflict` when copies still exist.
- Review visibility is always an explicit choice — never defaults to shared.

Full domain model: `docs/domain/entities.md`, `docs/domain/business-rules.md`
