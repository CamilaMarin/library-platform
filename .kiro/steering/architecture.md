---
inclusion: always
---

# Architecture — EntreLíneas

## Clean Architecture + lightweight DDD

```
Interface (API REST / Next.js)
    ↓
Application (use cases, interfaces for infrastructure)
    ↓
Domain (entities, value objects, business rules — zero external dependencies)
    ↓
Infrastructure (Postgres, encrypted storage, JWT auth — implements application interfaces)
```

## Rules

- The domain layer NEVER imports anything from frameworks or infrastructure.
- All business logic lives in the domain, not in controllers or infrastructure.
- Controllers never access the database directly — always through a use case.
- Use Dependency Injection for every external dependency.
- Every infrastructure dependency is accessed through abstractions (interfaces/protocols) defined in the application layer.
- The project is cloud agnostic — every service must be replaceable without touching domain or application code.

## Abstractions required (adr/0017)

- `FileStorage` → local filesystem, MinIO, S3, GCS, Supabase Storage
- `TokenService` → JWT implementation (PyJWT)
- `MetadataProvider` → Open Library, Google Books
- `NotificationService` → email, push (future)
- Repositories → via SQLAlchemy, behind protocol/interface

Reference: `adr/0017-cloud-agnostic-abstractions.md`

Full details: `docs/architecture/architecture.md`, `docs/architecture/coding-standards.md`
