# Requirements Document

## Introduction

This module coordinates book clubs within a family group: active book, discussion date, spoiler-safe comments, and digital reading turns that never move a file between accounts.

Source: `docs/specs/clubs.md`, `docs/domain/business-rules.md` (rule 3).

### Referenced ADRs
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0006-no-connected-groups-mvp.md` — Clubs only within a single family group in MVP
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation

## Glossary

- **Club**: coordination space within a single family group around an active book.
- **ReadingTurn**: mechanism coordinating who reads/comments on a digital book within a club, without transferring the file.

## Requirements

### Requirement 1: Book clubs

**User Story:** As a club organizer, I want to coordinate what's being read, when, and centralize comments, so we can foster conversation without losing track.

#### Acceptance Criteria
1. THE SYSTEM SHALL allow creating clubs within a family group.
2. THE SYSTEM SHALL allow assigning an active book and an estimated discussion date per club.
3. THE SYSTEM SHALL offer a comment space per book/club, with a `is_spoiler` flag (defaults to `false` — users must explicitly mark content as containing spoilers).
4. THE SYSTEM SHALL NOT require or facilitate transferring the digital file between club members; each member must have their own copy.

> Note: In the MVP, clubs can only exist within a single family group. "Connected groups" and multi-group clubs are removed from MVP per `adr/0006-no-connected-groups-mvp.md`.

### Requirement 2: Reading turn

**User Story:** As a club member, I want a fair, simple way to coordinate who reads and comments on a shared digital book, without anyone's file being copied or moved.

#### Acceptance Criteria
1. THE SYSTEM SHALL coordinate order and comments for a digital book via `ReadingTurn`, without moving the file between accounts.
2. THE SYSTEM SHALL validate that a user owns their own copy before activating their turn.
