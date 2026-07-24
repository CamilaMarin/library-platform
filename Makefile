.PHONY: up down test lint backend-test frontend-test backend-lint frontend-lint

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Run all tests
test: backend-test frontend-test

# Run all linters
lint: backend-lint frontend-lint

# Backend tests
backend-test:
	cd backend && python -m pytest

# Frontend tests
frontend-test:
	cd frontend && npm test

# Backend lint
backend-lint:
	cd backend && ruff check .

# Frontend lint
frontend-lint:
	cd frontend && npm run lint
