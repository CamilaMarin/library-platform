# Tech Stack — EntreLíneas

## Frontend
- Next.js + React + TypeScript
- Tailwind CSS
- epub.js (integrated EPUB reader)
- PDF.js (integrated PDF reader)

## Backend
- FastAPI (Python)
- SQLAlchemy (ORM)
- Alembic (migrations)
- PyJWT / python-jose (JWT tokens)

## Database
- PostgreSQL (strongly relational: users, groups, loans, permissions)

## Authentication
- Custom JWT: Access Token (short-lived) + Refresh Token (long-lived, rotatable).
- Supabase Auth, Cognito, and server-side sessions are intentionally rejected.
- Rationale: cloud agnostic, vendor neutral, portable, easy to test.
- See `adr/0004-custom-jwt-authentication.md`.

## Digital File Storage
- S3-compatible object storage, encrypted per user (server-side encryption by prefix/key).
- Local development: filesystem or MinIO via Docker.
- Accessed through `FileStorage` interface (cloud agnostic, see `adr/0017-cloud-agnostic-abstractions.md`).

## CI/CD
- GitHub Actions (lint, tests, build on every PR; deploy on merge to main).

## Containers
- Docker + Docker Compose for reproducible local development.

## Infrastructure Priority (zero-cost first)

```
Local (Docker)
   ↓
Supabase (Postgres + Storage, free tier — without Supabase Auth)
   ↓
Render / Vercel (API and frontend deploy)
   ↓
GCP / AWS (only if the project scales and justifies the cost)
```

See `adr/0002-tech-stack.md` for the full rationale.

## Testing
- Pytest (backend), focused on covering the domain layer without heavy mocking thanks to Clean Architecture.
- Integration tests for critical endpoints (auth, file access, ARCO, loans).

## Explicitly Excluded from MVP
- **Redis** — JWT doesn't require server-side state. May be introduced in v1+ for caching or rate limiting. See `adr/0012-no-redis-mvp.md`.

## Observability (v1+)
- Structured logging + the audit service already required by Ley 21.719 (Chile's Data Protection Law) serves as the foundation for data-access observability.
