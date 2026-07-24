---
inclusion: always
---

# Technology Stack — EntreLíneas

## Backend
- FastAPI (Python) + SQLAlchemy + Alembic
- PyJWT / python-jose (JWT tokens)
- Pytest (testing)
- Ruff + PEP8 (linting)

## Frontend
- Next.js + React + TypeScript + Tailwind
- epub.js (integrated EPUB reader)
- PDF.js (integrated PDF reader)
- ESLint + Prettier (linting)

## Database
- PostgreSQL

## Authentication
- JWT custom: Access Token (short-lived) + Refresh Token (long-lived, rotatable)
- NO Supabase Auth, NO Cognito, NO server-side sessions
- Reference: `adr/0004-custom-jwt-authentication.md`

## Storage
- Encrypted object storage, isolated per user (never shared between accounts)
- Local development: filesystem or MinIO via Docker
- Accessed via `FileStorage` interface (cloud agnostic)

## Containers
- Docker + Docker Compose for local development (mandatory)

## CI/CD
- GitHub Actions

## Commits
- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)

## Infrastructure priority (zero-cost first)
```
Local (Docker) → Supabase (Postgres + Storage, free tier) → Render/Vercel → GCP/AWS (only if justified)
```

## Explicitly excluded from MVP
- Redis (adr/0012) — JWT doesn't need server-side state
- Supabase Auth (adr/0004) — custom JWT only

Do not introduce alternatives to this stack without logging it as an ADR in `docs/adr/`.

References: `docs/architecture/tech-stack.md`, `adr/0002-tech-stack.md`, `adr/0004`, `adr/0012`
