# Requirements Document

## Introduction

This module covers personal library management: books (metadata of the intellectual work), copies (physical or digital instances owned by a user), search within the library, metadata import from external sources, and an integrated EPUB/PDF reader. Digital files are never exposed outside the account that uploaded them.

Reading selection (sorteo/draw) has its own dedicated spec: `.kiro/specs/reading-selection/`.

Source: `docs/domain/business-rules.md` (rules 1, 9, 11).

### Referenced ADRs
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation
- `adr/0010-search-in-library-module.md` — Search is part of Library
- `adr/0011-import-as-library-use-case.md` — Import is a Library use case
- `adr/0014-integrated-reader-mvp.md` — Integrated EPUB/PDF reader in MVP
- `adr/0015-book-copy-separation.md` — Book/Copy separation
- `adr/0017-cloud-agnostic-abstractions.md` — All infrastructure behind abstractions

## Glossary

- **Book**: catalog metadata of an intellectual work (title, author, genre, description). Independent of ownership. Can exist without copies.
- **Copy (Ejemplar)**: an instance of a Book owned by a User; physical (metadata + status only) or digital (encrypted file, isolated per account). Each copy has exactly one owner.
- **Reading Progress**: the user's current position in a digital copy, managed by the integrated reader.
- **Bookmark**: a saved position in a digital copy.
- **Note**: a text annotation associated with a position in a digital copy.

## Requirements

### Requirement 1: Book management

**User Story:** As a reader, I want to register the books I own (physical and digital), so I can see them all together and decide what to read.

#### Acceptance Criteria
1. THE SYSTEM SHALL allow creating a Book (metadata: title, author, genres, description, page count, ISBN) as a standalone action, independent of copy creation.
2. THE SYSTEM SHALL allow creating one or more Copies associated with a Book, as a separate explicit step after book creation.
3. WHEN a copy is "digital", THE SYSTEM SHALL store the encrypted file, associated only with the account that uploaded it.
4. WHEN a copy is "physical", THE SYSTEM SHALL store only metadata and availability status, with no file.
5. THE SYSTEM SHALL allow editing or deleting any book or copy at any time.

> Reference: `adr/0015-book-copy-separation.md` — Book represents the intellectual work, Copy represents an owned instance.

### Requirement 2: Metadata import

**User Story:** As a reader, I want to autocomplete book metadata from external sources, so I don't have to type everything manually.

#### Acceptance Criteria
1. IF the user searches by title or ISBN, THEN THE SYSTEM SHALL autocomplete metadata from a public source (e.g., Open Library), keeping file/copy creation as a separate step.
2. THE SYSTEM SHALL access external metadata sources through a replaceable abstraction (not coupled to a specific provider).

> Reference: `adr/0011-import-as-library-use-case.md`

### Requirement 3: Search

**User Story:** As a reader, I want to search for books within my personal library and my group's shared library (metadata), so I can quickly find what I'm looking for.

#### Acceptance Criteria
1. THE SYSTEM SHALL offer search within the user's own library by title, author, genre, and ISBN.
2. THE SYSTEM SHALL offer search within the user's group shared library (metadata only, never files).
3. Search results SHALL NEVER expose `file_ref` of digital copies belonging to other users.

> Reference: `adr/0010-search-in-library-module.md`

### Requirement 4: Integrated reader

**User Story:** As a digital reader, I want to open my EPUB/PDF files directly in the platform, with my progress saved.

#### Acceptance Criteria
1. THE SYSTEM SHALL include an integrated reader for EPUB and PDF files in the MVP.
2. THE SYSTEM SHALL only allow opening files uploaded by the authenticated user — never files belonging to another user.
3. THE SYSTEM SHALL store reading progress (position, percentage) associated with the user and the copy.
4. Reading progress IS personal data covered by Ley 21.719 (audit logging, ARCO export, deletion on cancellation).

> Reference: `adr/0014-integrated-reader-mvp.md`
> Full reader spec: `.kiro/specs/reader/`
> Note: Bookmarks and notes are deferred to v1 (reader-extras) per `docs/roadmap.md`.
