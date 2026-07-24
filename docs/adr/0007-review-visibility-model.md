# ADR-0007: Review Visibility Model

## Status
Accepted

## Context
The previous review visibility model (`private | group | club`) was ambiguous: a user can belong to multiple groups and clubs, and it wasn't clear which one each option referred to.

## Decision
Replace the visibility model with two fields:

- **visibility**: `private` | `shared`
- **shared_with**: explicit reference to a specific Group or a specific Club (only when `visibility = shared`)

## Consequences
- Eliminates ambiguity: every shared review indicates exactly who it's shared with.
- Database schema changes: `reviews.visibility` is replaced by `reviews.visibility` + `reviews.shared_with_type` + `reviews.shared_with_id`.
- The principle of "visibility is always explicitly decided by the author" (business rule 6) is reinforced by this model.
- A user can create multiple reviews of the same book with different visibilities, or a single review shared with one specific target.
