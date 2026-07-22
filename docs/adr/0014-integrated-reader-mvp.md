# ADR-0014: Integrated EPUB/PDF Reader in MVP

## Status
Accepted

## Context
It was debated whether the MVP should include an integrated reader or only library management (metadata). Since the value proposition includes "accompanying the reading experience," a basic reader reinforces the experience and justifies users uploading their files to the platform.

## Decision
- The MVP includes an **integrated EPUB and PDF reader**.
- The reader only opens files uploaded by the currently authenticated user (reinforces ADR-0001 and ADR-0009).
- Stored data: reading progress, bookmarks, and notes, associated with the user and the copy.

## Consequences
- A frontend EPUB/PDF rendering library is needed (epub.js, PDF.js).
- The backend must serve the encrypted file only to the owner (strict validation on the download endpoint).
- Additional entities are created: `ReadingProgress`, `Bookmark`, `Note` — associated with a digital Copy and its owner.
- Reader data (progress, notes) is personal data and is covered by Ley 21.719 (Chile's Data Protection Law): processing record, ARCO export, deletion on cancellation.
