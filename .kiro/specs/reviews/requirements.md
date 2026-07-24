# Requirements Document

## Introduction

This module implements book reviews with an explicit visibility model. Users can rate and review books, controlling exactly who sees each review.

Source: `docs/domain/entities.md`, `docs/domain/business-rules.md` (rule 6).

### Referenced ADRs
- `adr/0007-review-visibility-model.md` — Visibility: private | shared + explicit shared_with
- `adr/0003-ley-21719-compliance.md` — Reviews are personal data (audit log, ARCO export)

## Glossary

- **Review (Reseña)**: a user's rating + opinion about a book, with explicit visibility control.
- **Visibility**: `private` (only the author sees it) or `shared` (visible to a specific group or club).
- **shared_with**: when visibility is `shared`, the explicit target — a specific Group or a specific Club.

## Requirements

### Requirement 1: Create and manage reviews

**User Story:** As a reader, I want to rate and review books I've read, so I can remember my opinions and share them selectively.

#### Acceptance Criteria
1. THE SYSTEM SHALL allow creating a review with a rating (integer, 1–5) and optional text.
2. THE SYSTEM SHALL require an explicit visibility choice on every review: `private` or `shared`.
3. WHEN visibility is `shared`, THE SYSTEM SHALL require the user to specify exactly which Group or Club the review is shared with (`shared_with_type` + `shared_with_id`).
4. THE SYSTEM SHALL allow editing or deleting any review by its author.
5. THE SYSTEM SHALL NEVER default to a public or broadly-shared visibility — the user must always explicitly choose.

> Reference: `adr/0007-review-visibility-model.md`

### Requirement 2: Access control

**User Story:** As a reader, I want certainty that my reviews are only visible to those I choose.

#### Acceptance Criteria
1. THE SYSTEM SHALL only serve a `shared` review to members of the specified group or club.
2. THE SYSTEM SHALL return `private` reviews only to their author.
3. THE SYSTEM SHALL integrate with the Privacy module's visibility check before serving cross-user data.
