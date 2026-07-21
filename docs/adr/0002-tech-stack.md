# ADR-0002: Stack tecnológico y prioridad de infraestructura

## Estado
Aceptado

## Contexto
Dos conversaciones de planificación previas propusieron enfoques distintos de infraestructura: una sugería ir directo a GCP; la otra prioriza explícitamente costo cero (Local → Supabase → Render/Vercel → cloud pago solo si se justifica). Además, ambas coinciden en Clean Architecture, FastAPI y Next.js.

## Decisión
- **Backend:** FastAPI + SQLAlchemy + Alembic.
- **Frontend:** Next.js + React + TypeScript + Tailwind.
- **Base de datos:** PostgreSQL.
- **Infraestructura:** se prioriza costo cero — Local/Docker primero, luego Supabase (Postgres + Storage + Auth gestionados en free tier), luego Render/Vercel para deploy. GCP/AWS quedan como opción futura, solo si el proyecto escala más allá de lo que cubren los free tiers.
- Se reconcilia así la propuesta inicial de GCP: queda como destino posible a largo plazo, no como decisión de arranque.

## Consecuencias
- Menor fricción y costo para mantener el proyecto activo como pieza de portafolio.
- Supabase actúa como Postgres + Storage + Auth gestionados, reduciendo trabajo de infraestructura propia en las primeras fases.
- Si el proyecto migra a GCP/AWS más adelante, Clean Architecture (ADR implícito en `architecture/architecture.md`) permite que ese cambio no toque el domain layer.
