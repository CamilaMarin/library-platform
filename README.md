# EntreLíneas

A web platform for managing personal libraries (physical and digital) and fostering shared reading among families and small book clubs.

## Progress

| Milestone | Status |
|-----------|--------|
| M-1 Architecture Validation | ✅ Complete |
| M0 Privacy Foundation | ✅ Complete |
| M1 Authentication (JWT) | ✅ Complete |
| M2 Users & Groups | ✅ Complete |
| M3 Library (Books, Copies, Search) | ✅ Complete |
| M4 Reading Selection (Draw + Turn) | ✅ Complete |
| M5 Clubs & Reading Turns | ✅ Complete |
| M6 Reviews | ✅ Complete |
| M6.5 Frontend Catchup | ✅ Complete |
| M7 Loans | ✅ Complete |
| M8 Privacy Panel | ✅ Complete |
| M9 Release Candidate | In progress |

**11/12 milestones complete** · Architecture frozen · 17 ADRs · 10 specs

## Quick Start

```bash
docker compose up -d   # Start PostgreSQL + MinIO
cd backend
pip install -e ".[dev]"
alembic upgrade head   # Run migrations (currently at 0011)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

cd frontend
npm install
npm run dev            # Start frontend (port 3000)
```

Shortcuts:
```bash
make up        # Start infrastructure
make test      # Run all test suites
make lint      # Run linters (Ruff + ESLint)
make down      # Stop all services
```

### Production Deployment

```bash
cp backend/.env.example .env  # Set production secrets
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

See [docs/deployment.md](docs/deployment.md) for full guide.

## Features Implemented

- **Authentication:** JWT (Access + Refresh tokens), registration with consent gating, token rotation/revocation
- **Groups:** Family groups with invitation-based membership
- **Library:** Books + Copies (physical/digital), file upload with per-user isolation, search. Books can be created without copies (tagged as "want to read" automatically)
- **Reading Status:** Personal reading status per book (`want_to_read · reading · read · dnf`). One status per user/book pair — independent of copy count
- **Shelf View:** Library toggles between list view and bookshelf view. Shelf groups books by status as vertical spines on teak shelves. Preference persisted in `localStorage`
- **Reading Selection:** Filtered random draw + pick-by-turn with availability validation
- **Clubs:** Book clubs with active book, reading turns (ownership validated), spoiler-safe comments
- **Reviews:** Book reviews with explicit visibility control (private or shared with group/club), access-controlled listing, ARCO privacy integration
- **Privacy Foundation:** DataConsent, AuditLog (high-value operations), configurable RetentionPolicy
- **Privacy Panel (M8):** Full ARCO rights (export, rectify, delete, oppose), configurable retention job, field-level encryption infrastructure, data purge on account deletion, breach notification playbook
- **Visual Identity:** "Sala de lectura" design system — Walnut/Brass/Parchment palette, Playfair Display + Inter typography, CSS custom properties throughout
- **Frontend:** Complete Next.js UI — login/register, dashboard, library with shelf/list toggle, groups, reading selection, clubs, reviews, loans, settings (ARCO), privacy policy
- **Loans:** Loans page with active/returned tabs, library integration with copy status badges and inline loan form

## Architecture

```
Clean Architecture + DDD (lightweight)
├── Interface (FastAPI REST)
├── Application (use cases + protocols)
├── Domain (entities, no framework imports)
└── Infrastructure (PostgreSQL, MinIO, JWT)
```

Key decisions: [17 ADRs](docs/adr/) · Cloud agnostic · Ley 21.719 compliance from day one

## Project Documentation

- **[docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)** — complete project overview (start here)
- **[docs/architecture/](docs/architecture/)** — architecture, tech stack, API, database
- **[.kiro/specs/](.kiro/specs/)** — implementation specifications (source of truth)
- **[docs/adr/](docs/adr/)** — architecture decision records
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** — detailed progress tracking
- **[CHANGELOG.md](CHANGELOG.md)** — what was delivered per milestone

## Structure

```
backend/           FastAPI + SQLAlchemy + Alembic
  app/
    identity/      Authentication, users, groups
    library/       Books, copies, reading status, file storage
    community/     Clubs, reading turns, comments
    reviews/       Book reviews with visibility control
    reading_selection/  Draw, pick-by-turn
    circulation/   Loans
    auth/          JWT utilities
frontend/          Next.js + React + TypeScript + Tailwind
  src/
    app/           Pages (library, loans, reviews, groups, clubs, settings…)
    components/    Shared components (BookSpine, BookShelf, Navigation…)
    lib/           API client, token storage
    types/         TypeScript contracts
docs/              Project documentation
.kiro/             Specifications + steering rules
```

## Development

Requires: Docker, Docker Compose, Python 3.12+, Node.js 20+.

See `docs/ai/DEVELOPMENT_WORKFLOW.md` for contribution workflow.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Alembic, PyJWT, bcrypt
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind, Lucide icons
- **Database:** PostgreSQL 16
- **Storage:** MinIO (S3-compatible, per-user isolation)
- **CI:** GitHub Actions (Ruff + Pytest + ESLint)
- **Containers:** Docker Compose
