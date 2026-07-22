# ADR-0002: Technology Stack and Infrastructure Priority

## Status
Accepted

## Context
Two prior planning conversations proposed different infrastructure approaches: one suggested going straight to GCP; the other explicitly prioritized zero-cost (Local → Supabase → Render/Vercel → paid cloud only if justified). Both agreed on Clean Architecture, FastAPI, and Next.js.

## Decision
- **Backend:** FastAPI + SQLAlchemy + Alembic.
- **Frontend:** Next.js + React + TypeScript + Tailwind.
- **Database:** PostgreSQL.
- **Infrastructure:** zero-cost priority — Local/Docker first, then Supabase (Postgres + Storage as managed free tier), then Render/Vercel for deploy. GCP/AWS remain as a future option, only if the project scales beyond what free tiers cover.
- This reconciles the initial GCP proposal: it stays as a possible long-term destination, not as the starting decision.

## Consequences
- Lower friction and cost to keep the project active as a portfolio piece.
- Supabase acts as managed Postgres + Storage, reducing infrastructure overhead in early phases.
- If the project migrates to GCP/AWS later, Clean Architecture (see `adr/0017`) ensures that change doesn't touch the domain layer.
