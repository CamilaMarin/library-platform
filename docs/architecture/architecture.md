# Architecture — EntreLíneas

## Style: Clean Architecture + Domain-Driven Design (lightweight)

```
┌─────────────────────────────────────────────┐
│  Interface layer                             │
│  REST API (FastAPI) · Web (Next.js)          │
└───────────────────┬───────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Application layer                           │
│  Use cases (see domain/use-cases.md)         │
│  Interfaces/protocols for infrastructure     │
└───────────────────┬───────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Domain layer                                │
│  Entities, value objects, business rules     │
│  No external dependencies (no DB, no HTTP)   │
└───────────────────┬───────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Infrastructure layer                        │
│  PostgreSQL · Encrypted storage · JWT Auth   │
│  Concrete implementations of interfaces      │
└─────────────────────────────────────────────┘
```

Hard rule: the domain never imports anything from infrastructure or frameworks. Infrastructure implements interfaces defined by the domain/application (Dependency Inversion). See `adr/0017-cloud-agnostic-abstractions.md`.

## Bounded Contexts

1. **Identity & Privacy** — User, DataConsent, RefreshToken, ARCO rights.
2. **Library** — Book, Copy, ReadingProgress, Bookmark, Note, isolated per-user storage, integrated reader.
3. **Community** — FamilyGroup, Club, ReadingTurn. Clubs only within a family group in the MVP.
4. **Circulation** — Loan (physical only).
5. **Reviews** — Review, with visibility `private | shared` and explicit target.
6. **Reading Selection** — Draw, per-participant availability. Dedicated spec.

Each context can evolve relatively independently; they share identifiers (user_id, book_id) but not internal logic.

## Infrastructure Abstractions (cloud agnostic — see adr/0017)

Every external dependency is accessed through interfaces defined in the application layer:

- `FileStorage` → implementations: local filesystem, MinIO, S3, GCS, Supabase Storage.
- `TokenService` → implementation: JWT (PyJWT).
- `MetadataProvider` → implementations: Open Library, Google Books.
- `NotificationService` → interchangeable implementations (email, push, etc.).
- Repositories (via SQLAlchemy) → abstracted by protocol/interface.

## High-Level Infrastructure Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Next.js    │────▶│  FastAPI (REST)   │────▶│  PostgreSQL         │
│  (web)      │◀────│  + JWT Auth       │◀────│                     │
└─────────────┘     └──────────────────┘     └───────────────────┘
       │                      │
       │             ┌────────┴────────┐
       │             ▼                 ▼
       │    ┌─────────────────┐  ┌──────────────────┐
       │    │ Encrypted        │  │ Audit/logging     │
       │    │ storage isolated │  │ service           │
       │    │ per user         │  │ (Ley 21.719)      │
       │    └─────────────────┘  └──────────────────┘
       │
       ▼
┌─────────────────┐
│ EPUB/PDF Reader │
│ (epub.js/PDF.js)│
└─────────────────┘
```

## Why Clean Architecture (and not something simpler)

The project is also a portfolio piece: it demonstrates layer separation, domain testability without mocking infrastructure, and a foundation that survives a framework or cloud provider change without rewriting business rules. See `adr/0002-tech-stack.md` and `adr/0017-cloud-agnostic-abstractions.md`.
