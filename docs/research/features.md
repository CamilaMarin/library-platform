# Research — Feature Backlog

Backlog classified by version. Base categories from the brainstorming session, adjusted to product principles (closed circle, no file sharing, privacy by design).

## MVP (Phase 1)

- **Books / Library**: book creation (intellectual work metadata), physical and digital copies (Book/Copy separated model), editing and deletion. Search and import as Library use cases (see `adr/0010`, `adr/0011`).
- **Integrated Reader**: EPUB/PDF reader built into the platform, reading progress, bookmarks, and notes. Owner's files only (see `adr/0014`).
- **Groups**: family group creation, invitation with explicit acceptance. No adult/minor distinction in MVP (see `adr/0005`).
- **Reading Selection (Sorteo)**: filterable random draw (genre, pages, availability for all, unread), pick-by-turn mode. Dedicated spec (see `adr/0013`). Availability = authorized access per participant (see `adr/0008`).
- **Clubs**: club creation within a family group (not across groups in MVP, see `adr/0006`), active book, discussion date, comments with spoiler marking.
- **Loans (Préstamos)**: physical copy lending, digital reading turns (no file transfer).
- **Reviews (Reseñas)**: rating (integer 1–5) + opinion, with visibility `private | shared` and explicit target (specific group or club, see `adr/0007`).
- **Privacy**: explicit consent, self-service ARCO rights, processing record, audit logs, configurable retention (see `adr/0016`).
- **Authentication**: custom JWT with Access Token + Refresh Token (see `adr/0004`). No Redis (see `adr/0012`).
- **Search (Búsqueda)**: basic search within personal and group library (metadata only). Part of Library.
- **Import**: manual entry + metadata autocomplete (ISBN/title via public source like Open Library). Part of Library.

## v1 (Phase 2)

- **Bookmarks / Highlights / Notes (advanced)**: extended reader functionality.
- **Reading Sessions (Sesiones de Lectura)**: reading session tracking (time, pages), base for statistics.
- **Goals (Metas)**: personal or group reading goals (e.g., "read 12 books this year").
- **Statistics (Estadísticas)**: pages read, books by genre, reading pace.
- **Export**: general data export beyond ARCO minimum (e.g., full JSON backup).
- **Notifications (Notificaciones)**: club reminders, loan returns, reading turns.
- **Redis**: caching, rate limiting, features that justify it.

## v2 (Phase 3)

- **Authors / Series / Publishers / Collections**: catalog metadata enrichment, themed lists.
- **Minor accounts (Cuentas de menores)**: minor accounts with responsible adult, differentiated permissions (see `adr/0005`).
- **Connected groups (Grupos conectados)**: potentially extending clubs beyond a family group (requires prior design, see `adr/0006`).
- **Challenges (Retos)**: group reading challenges with shared progress.
- **Achievements (Logros)**: badges for reading milestones (optional, avoiding distracting gamification).

## Future (no committed date)

- **Recommendations (Recomendaciones)**: recommendation engine, potentially AI-based, from personal and group history.
- **Extended connected groups**: extending beyond the family core while maintaining the closed-circle model (never a public network). Requires `product-principles.md` review before implementation.

## Explicitly Discarded

- Public feed / open social discovery.
- Any form of digital file sharing or transfer between accounts (see `adr/0001-no-shared-file-storage.md`).
