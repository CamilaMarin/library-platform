# PROJECT_CONTEXT.md — EntreLíneas

> Level-1 entry document. Any person or AI agent (Claude, Kiro, etc.) should be able to understand the entire project by reading only this file. To implement a specific module, also load `.kiro/specs/<module>/`, the related entities in `domain/entities.md`, and the rules in `domain/business-rules.md` (Level 2).

## 1. Executive Summary

EntreLíneas is a web platform for managing personal libraries (physical and digital) and fostering shared reading among families and small book clubs within a family group.

It does not compete with Goodreads or Kindle. The goal is to connect people through stories, not to accumulate a public network of readers.

The platform enables: registering physical books, managing personal EPUB/PDF files (never shared between accounts), creating family groups, organizing book clubs within the group, tracking physical loans and digital reading turns, reading with an integrated reader, commenting and reviewing, selecting joint readings via draw, and exercising full control over personal data (Ley 21.719, Chile's Data Protection Law).

## 2. Product Vision

Stories bring people together. EntreLíneas aims to be the digital home where people manage their library and share the experience of reading together. The primary focus is families and small book clubs — not the general reading public.

See detail in `vision.md`.

## 3. Product Principles

1. People come before books.
2. The user owns their library and their data.
3. Privacy by Design (Ley 21.719 from the first sprint).
4. The app accompanies reading, it doesn't replace it.
5. Everything should feel close and simple, even if the function is complex.
6. Cloud-agnostic and zero-cost by default.
7. Mobile-first.

See detail in `product-principles.md`.

## 4. The Problem

A family with hundreds of physical and digital books had no simple way to: know what books they had, share the library, organize a book club, choose the next book, record opinions, or manage loans. Current solutions (Goodreads, StoryGraph, Calibre, Komga, Kavita, Audiobookshelf) cover parts of the problem — none bring them all together simply and privately. Full detail in `research/competitors.md`.

## 5. Target Users

Reading families (primary case), small book clubs within a family group, individual readers within a family group. Detail in `research/users.md`.

## 6. Domain (summary)

User · FamilyGroup · Book · Copy (physical/digital) · Club · ReadingTurn · Loan · Review · DataConsent · ReadingProgress · Bookmark · Note

MVP social hierarchy: **User → Group → Shared Library** (metadata). No "connected groups" in the MVP.

Full detail in `domain/entities.md`, `domain/business-rules.md`, `domain/use-cases.md`.

## 7. Architecture (summary)

```
Interface (REST API / Next.js)
      ↓
Application (use cases)
      ↓
Domain (entities, business rules — no external dependencies)
      ↓
Infrastructure (Postgres, encrypted storage, JWT auth)
```

Clean Architecture: the domain never depends on frameworks or the database. Every external dependency is accessed through abstractions (interfaces) defined in the application layer. See `adr/0017-cloud-agnostic-abstractions.md`.

Detail in `architecture/architecture.md`.

## 8. Stack

- **Frontend:** Next.js, React, TypeScript, Tailwind.
- **Backend:** FastAPI (Python), SQLAlchemy, Alembic.
- **Database:** PostgreSQL.
- **Authentication:** Custom JWT (Access Token + Refresh Token). See `adr/0004-custom-jwt-authentication.md`.
- **Digital file storage:** encrypted object storage per user (never shared between accounts).
- **CI/CD:** GitHub Actions.
- **Containers:** Docker / Docker Compose.
- **Integrated reader:** EPUB (epub.js) + PDF (PDF.js). See `adr/0014-integrated-reader-mvp.md`.

> **Note:** Redis is not part of the MVP (see `adr/0012-no-redis-mvp.md`). It may be introduced in future versions.

Detail and rationale in `architecture/tech-stack.md` and `adr/0002-tech-stack.md`.

## 9. Infrastructure — Cost Priority

```
Local (Docker) → Supabase (Postgres + Storage, free tier) → Render / Vercel (deploy) → GCP/AWS (only if the project scales and justifies it)
```

> Supabase Auth was rejected — custom JWT is used. Supabase remains only as a managed Postgres + Storage option.

## 10. Permanent Constraints

- Never store or distribute a copyrighted digital file between different user accounts.
- Do not use paid services by default; prefer open source and free tiers.
- Every external integration must have an interface (replaceable, not coupled to a provider).
- Every infrastructure dependency behind abstractions — always cloud agnostic.
- Comply with Ley 21.719 (Chile's Data Protection Law) from design: data minimization, explicit consent, self-service ARCO rights, breach notification in 72h, configurable retention.
- A loan can only be registered for a physical copy. Digital books are coordinated via "reading turns," never by transferring the file.
- The integrated reader only opens files belonging to the currently authenticated user.
- Do not hardcode retention periods — they must be configurable.

## 11. MVP Scope Decisions

- Minor accounts: **deferred to v2**. All MVP users share the same permission model.
- Connected groups: **removed from MVP**. Only the hierarchy User → Group → Shared Library exists.
- Clubs: only within a family group (not across different groups in the MVP).
- Redis: removed from MVP. JWT doesn't require server-side state.
- Search and Import: part of the Library module, not independent modules.
- Reading Selection (draw): dedicated spec due to its complexity.

## 12. Conventions

REST + JSON · OpenAPI auto-generated (FastAPI) · Conventional Commits · PEP8 + Ruff (backend) · ESLint + Prettier (frontend) · Pytest · Docker mandatory for local development.

## 13. Roadmap (summary)

MVP → v1 → v2 → Future. Full detail in `roadmap.md` and `research/features.md`.

## 14. AI Agent Rules (Steering)

See `steering-rules.md` — permanent rules that don't change between tasks (Clean Architecture, mandatory testing, dependency injection, etc.). Always loaded alongside this document.

## 15. Document Map

```
docs/
├── PROJECT_CONTEXT.md      ← you are here
├── vision.md
├── product-principles.md
├── roadmap.md
├── glossary.md
├── steering-rules.md
├── research/{competitors,users,features}.md
├── architecture/{architecture,tech-stack,coding-standards,api,database}.md
├── ux/{sitemap,user-flows,wireframes}.md
├── domain/{entities,business-rules,use-cases}.md
└── adr/0001-0017*.md

.kiro/
├── specs/{authentication,library,clubs,loans,privacy,reading-selection,reviews}/
└── steering/*.md (10 files, auto-loaded by Kiro)
```
