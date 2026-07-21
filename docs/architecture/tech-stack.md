# Tech Stack — EntreLíneas

## Frontend
- Next.js + React + TypeScript
- Tailwind CSS
- epub.js (lector EPUB integrado)
- PDF.js (lector PDF integrado)

## Backend
- FastAPI (Python)
- SQLAlchemy (ORM)
- Alembic (migraciones)
- PyJWT / python-jose (JWT tokens)

## Base de datos
- PostgreSQL (naturaleza fuertemente relacional: usuarios, grupos, préstamos, permisos)

## Autenticación
- JWT custom: Access Token (corta duración) + Refresh Token (larga duración, rotable).
- No se usa Supabase Auth, Cognito ni sesiones server-side.
- Justificación: cloud agnostic, vendor neutral, portable, fácil de testear.
- Ver `adr/0004-custom-jwt-authentication.md`.

## Storage de archivos digitales
- Object storage compatible S3, cifrado por usuario (server-side encryption por prefijo/clave).
- En desarrollo local: filesystem o MinIO vía Docker.
- Accedido a través de interfaz `FileStorage` (cloud agnostic, ver `adr/0017-cloud-agnostic-abstractions.md`).

## CI/CD
- GitHub Actions (lint, tests, build en cada PR; deploy en merge a main).

## Contenedores
- Docker + Docker Compose para desarrollo local reproducible.

## Prioridad de infraestructura (costo cero primero)

```
Local (Docker)
   ↓
Supabase (Postgres + Storage, free tier — sin Supabase Auth)
   ↓
Render / Vercel (deploy de API y frontend)
   ↓
GCP / AWS (solo si el proyecto escala y lo justifica económicamente)
```

Ver `adr/0002-tech-stack.md` para la justificación completa.

## Testing
- Pytest (backend), con foco en cubrir el domain layer sin mocks pesados gracias a Clean Architecture.
- Tests de integración para endpoints críticos (auth, préstamos, ARCO).

## Explícitamente excluido del MVP
- **Redis** — JWT no requiere estado server-side. Podrá introducirse en v1+ para cache o rate limiting. Ver `adr/0012-no-redis-mvp.md`.

## Observabilidad (v1+)
- Logging estructurado + el servicio de auditoría ya exigido por Ley 21.719 (ver `specs/privacy.md`) sirve como base de observabilidad de acceso a datos.
