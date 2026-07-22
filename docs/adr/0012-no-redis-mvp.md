# ADR-0012: Redis Removed from MVP

## Status
Accepted

## Context
The original stack included Redis as a "v1+" dependency for sessions, draw result caching, and rate limiting. With the decision to use JWT (ADR-0004), the primary motivator for Redis in the MVP (sessions) disappears.

## Decision
- Redis is removed from the MVP.
- JWT authentication does not require server-side session storage.
- Redis may be introduced in future versions for caching, rate limiting, or features that justify it.

## Consequences
- Reduces docker-compose complexity for development (fewer services).
- Rate limiting in the MVP is implemented in-memory or with lightweight stateless solutions (middleware).
- If JWT token revocation before expiration is needed, a blocklist in PostgreSQL will be evaluated before introducing Redis.
