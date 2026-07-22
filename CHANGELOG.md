# Changelog — EntreLíneas

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [M-1] — Architecture Validation

### Added
- Docker Compose with PostgreSQL 16 and MinIO (S3-compatible local storage)
- FastAPI backend skeleton with SQLAlchemy and Alembic
- `GET /health` endpoint with database connectivity check
- JWT utility proof-of-concept (PyJWT: create, verify, expiry, tamper detection)
- Next.js + TypeScript + Tailwind frontend skeleton
- Frontend /health call displaying backend status
- CORS middleware for local development
- GitHub Actions CI workflow (Ruff lint + Pytest)
- .env-based configuration (DATABASE_URL)
- Makefile with `up`, `down`, `test`, `lint` shortcuts

### Validated
- Full stack e2e: Docker → PostgreSQL → FastAPI → Next.js
- JWT issuance and verification works with PyJWT
- Alembic migrations run against Docker PostgreSQL
- 4 tests passing, lint clean
