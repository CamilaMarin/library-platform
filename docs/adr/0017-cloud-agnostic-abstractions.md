# ADR-0017: Cloud Agnostic — All Dependencies Behind Abstractions

## Status
Accepted

## Context
Complements and formalizes product principle 7 ("Cloud-agnostic and zero-cost by default") and ADR-0002 (infrastructure priority) as an explicit architectural constraint.

## Decision
- The entire project must remain **cloud agnostic**.
- Every infrastructure dependency must be **replaceable** without modifying the domain or application layer.
- Every external service must be accessed through **abstractions** (interfaces/protocols defined in the application layer, implemented in infrastructure).

## Consequences
- File storage: `FileStorage` interface → implementations: local filesystem, MinIO, S3, GCS, Supabase Storage.
- Database: SQLAlchemy as abstraction over PostgreSQL (portable to other SQL engines if needed).
- Email/notifications: `NotificationService` interface → interchangeable implementations.
- No proprietary cloud SDK is used directly in application/domain layers.
- The local docker-compose development environment is the reference implementation — any cloud deploy is just another implementation of the same interfaces.
