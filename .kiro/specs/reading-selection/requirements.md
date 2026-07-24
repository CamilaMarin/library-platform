# Requirements Document

## Introduction

This module implements joint reading selection: a filtered random draw and an alternative pick-by-turn mode. It helps family groups decide what to read together. The availability rule ensures every participant has authorized access to the selected book.

Source: `docs/domain/business-rules.md` (rule 8), `adr/0008-reading-selection-availability.md`.

### Referenced ADRs
- `adr/0008-reading-selection-availability.md` — Availability rule defined
- `adr/0013-reading-selection-dedicated-spec.md` — Dedicated specification for this feature
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation
- `adr/0015-book-copy-separation.md` — Book/Copy model

## Glossary

- **Draw (Sorteo)**: filtered random selection mechanism for joint reading choice within a group.
- **Availability**: each selected participant must have authorized access to the chosen book — physical copy available (not on loan) or digital copy personally owned.

## Requirements

### Requirement 1: Random draw

**User Story:** As a family group member, I want the app to help us choose what to read together, fairly and with filters, so we don't get stuck with too many options.

#### Acceptance Criteria
1. THE SYSTEM SHALL offer a random draw filterable by: genre, maximum page count, availability for all selected participants, and books not previously read by the group.
2. WHEN a draw runs, THE SYSTEM SHALL show which personal library each candidate book comes from, without exposing digital files.
3. THE SYSTEM SHALL apply the availability rule: a book can only be a candidate if every selected participant has authorized access to it.
4. For physical books, "authorized access" means an available copy (status != `on_loan`) accessible to the participant.
5. For digital books, "authorized access" means the participant personally owns their own copy.
6. THE SYSTEM SHALL NEVER offer access to another user's digital file as a way to satisfy availability.

> Reference: `adr/0008-reading-selection-availability.md`

### Requirement 2: Pick by turn

**User Story:** As a family group member, I want an alternative mode where we take turns choosing the next book, so everyone gets a say.

#### Acceptance Criteria
1. THE SYSTEM SHALL offer a "pick by turn" mode that rotates which member chooses the next book.
2. THE SYSTEM SHALL track turn history so the rotation is fair.
