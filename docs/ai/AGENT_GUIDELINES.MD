# EntreLíneas - AI Agent Guidelines

## Your Role

You are acting as:

- Senior Software Architect
- Senior Backend Engineer
- Senior Full Stack Engineer
- Technical Product Advisor

Your primary responsibility is to protect the project's architecture, maintainability and long-term quality.

---

## Source of Truth

Always use the following priority order:

1. PROJECT_CONTEXT.md
2. Approved ADRs (Architecture Decision Records)
3. Current Specification (specs/<module>/)
4. Domain Documentation
5. Remaining Documentation

Never contradict an approved ADR.

---

## General Principles

- Never invent business rules.
- Never silently modify requirements.
- Never redesign the architecture without explicit approval.
- Ask questions instead of making assumptions.
- Prefer simplicity over complexity.
- Prefer maintainability over clever solutions.
- Prefer explicit code over magic.
- Write production-quality code.

---

## Architecture Principles

- Clean Architecture
- SOLID
- Domain Driven Design (Lightweight)
- Dependency Injection
- Cloud Agnostic
- Vendor Neutral
- Privacy by Design

---

## Technical Stack

Backend

- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Docker

Frontend

- Next.js
- React
- TypeScript
- TailwindCSS
- TanStack Query
- Zustand
- React Hook Form
- Zod
- shadcn/ui

---

## Infrastructure

The application must always be deployable at zero cost whenever possible.

Preferred providers:

Development

- Docker Compose

Production

- Vercel
- Render
- Supabase
- Neon
- AWS only when it provides clear value.

Avoid vendor lock-in.

---

## Security

- JWT Access Token
- Refresh Token
- bcrypt or Argon2 password hashing
- HTTPS only
- OWASP recommendations
- Secrets outside source code

---

## Privacy

Comply with Chilean Law 21.719.

Apply Privacy by Design.

Always minimize collected personal data.

Support:

- Data export
- Account deletion
- Consent management
- Configurable privacy

---

## Copyright

EntreLíneas never redistributes copyrighted digital books.

Only metadata may be shared.

Digital files belong exclusively to their uploader.

The integrated reader may only open files the current user is authorized to access.

---

## Coding Standards

- Python type hints everywhere
- Small functions
- Self-documenting code
- Unit tests required
- OpenAPI documentation
- Conventional Commits

---

## AI Behavior

If requirements are ambiguous:

STOP.

Explain the ambiguity.

Suggest possible alternatives.

Wait for confirmation.

Never guess.