# Deployment Guide — EntreLíneas

## Prerequisites

- Docker & Docker Compose v2+
- A `.env` file with production secrets (see below)

## Environment Variables

Copy `backend/.env.example` to `.env` at the project root and set production values:

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_PASSWORD` | Database password | ✅ |
| `JWT_SECRET_KEY` | Random 32+ char secret for JWT signing | ✅ |
| `ENCRYPTION_KEY` | Fernet key for PII encryption (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) | ✅ |
| `MINIO_ROOT_PASSWORD` | MinIO storage password | ✅ |
| `POSTGRES_USER` | Database user (default: `entrelineas`) | |
| `POSTGRES_DB` | Database name (default: `entrelineas`) | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token TTL (default: 30) | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL (default: 7) | |
| `NEXT_PUBLIC_API_URL` | Backend URL as seen by the browser (default: `http://localhost:8000`) | |
| `APP_VERSION` | Version string (default: `1.0.0`) | |

## Deploy with Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/CamilaMarin/library-platform.git
cd library-platform

# 2. Create .env with production secrets
cp backend/.env.example .env
# Edit .env with real values (POSTGRES_PASSWORD, JWT_SECRET_KEY, etc.)

# 3. Build and start all services
docker compose -f docker-compose.prod.yml up --build -d

# 4. Run database migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 5. Verify
curl http://localhost:8000/health
# Should return: {"status":"ok","database":"healthy","version":"1.0.0"}

# Frontend available at http://localhost:3000
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js app (standalone mode) |
| `backend` | 8000 | FastAPI REST API |
| `postgres` | 5432 (internal) | PostgreSQL 16 database |
| `minio` | 9000/9001 (internal) | S3-compatible object storage |

## Database Migrations

Migrations run automatically on first deploy. For subsequent deployments:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

To check current migration state:
```bash
docker compose -f docker-compose.prod.yml exec backend alembic current
```

## Updating

```bash
git pull origin master
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Monitoring

- **Health check:** `GET /health` returns database connectivity status
- **API docs:** `GET /docs` (Swagger UI) — disable in production if needed
- **Logs:** `docker compose -f docker-compose.prod.yml logs -f backend`

## Security Checklist

Before going live:

- [ ] Set strong `POSTGRES_PASSWORD` (20+ random chars)
- [ ] Set strong `JWT_SECRET_KEY` (32+ random chars)
- [ ] Generate a proper `ENCRYPTION_KEY` with Fernet
- [ ] Set strong `MINIO_ROOT_PASSWORD`
- [ ] Set `NEXT_PUBLIC_API_URL` to the actual production backend URL
- [ ] Enable HTTPS via reverse proxy (nginx, Caddy, or cloud LB)
- [ ] Restrict CORS origins in `backend/app/main.py` to production domain
- [ ] Remove or restrict `/docs` endpoint in production
- [ ] Set up database backups (pg_dump cron or managed service)
- [ ] Review Ley 21.719 compliance: breach notification contacts configured

## Local Development (unchanged)

For local development, continue using the original docker-compose.yml:

```bash
docker compose up -d          # Start Postgres + MinIO
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev    # Port 3000
```
