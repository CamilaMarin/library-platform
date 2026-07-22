# EntreLíneas

A web platform for managing personal libraries (physical and digital) and fostering shared reading among families and small book clubs.

## Quick Start

```bash
make up        # Start all services (Postgres, MinIO, backend, frontend)
make test      # Run all test suites
make lint      # Run linters (Ruff + ESLint)
make down      # Stop all services
```

## Project Documentation

For full project context, architecture, and specifications, see:

- **[docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)** — complete project overview (start here)
- **[docs/architecture/](docs/architecture/)** — architecture, tech stack, API, database
- **[.kiro/specs/](/.kiro/specs/)** — implementation specifications (source of truth)
- **[docs/adr/](docs/adr/)** — architecture decision records

## Structure

```
backend/       FastAPI + SQLAlchemy + Alembic
frontend/      Next.js + React + TypeScript + Tailwind
docs/          Project documentation
.kiro/         Kiro specifications and steering rules
```

## Development

Requires: Docker, Docker Compose, Python 3.12+, Node.js 20+.

See `docs/ai/DEVELOPMENT_WORKFLOW.md` for contribution workflow.
