# ADR-0013: Reading Selection as Dedicated Specification

## Status
Accepted

## Context
Reading selection (filterable random draw, pick-by-turn mode) is a core MVP feature that differentiates EntreLíneas from competitors. It was briefly described within the library spec but deserves independent treatment given its complexity (filters, availability validation, multiple selection modes).

## Decision
- Create a dedicated specification for Reading Selection: `.kiro/specs/reading-selection/` with requirements, design, and tasks.

## Consequences
- Reading selection acceptance criteria move out of the library spec into their own spec.
- The library spec focuses exclusively on library management (CRUD for books and copies, search, import, reader).
- The bounded context remains Library at implementation level (reading selection uses Book/Copy entities), but it has its own functional specification.
