# ADR-0004: Custom JWT Authentication

## Status
Accepted

## Context
The project needs an authentication mechanism. Options evaluated: Supabase Auth (managed service), AWS Cognito (cloud-specific), server-side sessions (require shared state/Redis), and custom JWT (stateless, portable).

## Decision
- Implement custom authentication based on **JWT Access Tokens + Refresh Tokens**.
- Explicitly rejected: Supabase Auth, AWS Cognito, and server-side sessions.

## Rationale
- **Cloud agnostic:** not tied to any external identity provider.
- **Vendor neutral:** the mechanism is standard (RFC 7519) and portable across any infrastructure.
- **Portable:** deployable on local Docker, Render, Vercel, GCP, or AWS without changing the auth system.
- **Easy to test:** no mocks of external services needed for auth integration tests.
- **Learning experience:** implementing auth from scratch adds portfolio value.

## Consequences
- Eliminates the Supabase Auth dependency mentioned in `adr/0002-tech-stack.md` — Supabase remains only as a Postgres + Storage option.
- Redis is not needed for sessions in the MVP (see `adr/0012`).
- Requires implementing Refresh Token rotation, revocation, and secure client-side token storage.
- The domain layer remains unaware of JWT — the logic lives in infrastructure/interface layers.
