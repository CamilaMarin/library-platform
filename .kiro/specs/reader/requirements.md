# Requirements Document

## Introduction

This module implements an integrated EPUB/PDF reader that allows users to read their own digital files directly in the platform with automatic progress tracking. Bookmarks and notes are deferred to v1 (reader-extras).

Source: `docs/domain/business-rules.md` (rule 9).

### Referenced ADRs
- `adr/0014-integrated-reader-mvp.md` — Integrated EPUB/PDF reader in MVP
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation
- `adr/0017-cloud-agnostic-abstractions.md` — All infrastructure behind abstractions

## Glossary

- **Reader**: the in-browser component that renders EPUB/PDF files for the authenticated owner.
- **ReadingProgress**: the user's current position in a digital copy (position, percentage, last read timestamp).
- **CFI (Canonical Fragment Identifier)**: EPUB standard for referencing a position within the book structure.

## Requirements

### Requirement 1: File serving with ownership validation

**User Story:** As a digital reader, I want to open my EPUB/PDF files directly in the platform, knowing only I can access my files.

#### Acceptance Criteria
1. THE SYSTEM SHALL serve the encrypted digital file to the authenticated owner via `GET /copies/{id}/file`.
2. THE SYSTEM SHALL reject any attempt to access a file where `request.user_id != copy.user_id` with `403 Forbidden`.
3. THE SYSTEM SHALL validate ownership at the application layer, not only at the UI level.
4. THE SYSTEM SHALL support EPUB and PDF file formats.
5. THE SYSTEM SHALL stream files efficiently without loading the entire file into memory.

### Requirement 2: Reading progress persistence

**User Story:** As a digital reader, I want my reading position saved automatically so I can resume where I left off.

#### Acceptance Criteria
1. THE SYSTEM SHALL store reading progress (position, percentage, last_read_at) associated with the user and the copy.
2. THE SYSTEM SHALL allow retrieving the last saved progress via `GET /copies/{id}/progress`.
3. THE SYSTEM SHALL allow saving/updating progress via `PUT /copies/{id}/progress`.
4. THE SYSTEM SHALL use CFI-based positioning for EPUB files and page-based positioning for PDF files.
5. Reading progress IS personal data covered by Ley 21.719 (Chile's Data Protection Law) — audit logging and ARCO export apply.

### Requirement 3: Frontend reader rendering

**User Story:** As a digital reader, I want the reading experience to be smooth and responsive in my browser.

#### Acceptance Criteria
1. THE SYSTEM SHALL render EPUB files using epub.js (or equivalent library accessed via abstraction).
2. THE SYSTEM SHALL render PDF files using PDF.js (or equivalent library accessed via abstraction).
3. THE SYSTEM SHALL auto-save progress at configurable intervals (e.g., every page turn or every 30 seconds).
4. THE SYSTEM SHALL restore the user's last position when opening a previously-read file.

> Note: Bookmarks and notes are deferred to v1 (reader-extras) per `docs/roadmap.md`.
