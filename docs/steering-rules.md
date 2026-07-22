# Steering Rules — EntreLíneas

> Permanent rules for any AI agent (Kiro, Claude Code, etc.) implementing on this project. Always loaded alongside `PROJECT_CONTEXT.md`, regardless of the task's module.

## Architecture & Code

1. Follow Clean Architecture: the domain layer never imports framework or infrastructure.
2. All business logic lives in the domain, not in controllers or the infrastructure layer.
3. Never access the database directly from controllers — always through a use case.
4. Use Dependency Injection for every external dependency.
5. Every infrastructure dependency is accessed through abstractions (interfaces/protocols). The project is cloud agnostic — see `adr/0017-cloud-agnostic-abstractions.md`.
6. Every new feature requires tests (domain + integration) before being considered done.
7. Do not add new libraries without justifying why existing packages are insufficient.
8. Prioritize clarity over premature optimization.

## Security & Privacy

9. Never implement any form of digital file storage or transfer shared between user accounts (see `adr/0001-no-shared-file-storage.md`) — no exceptions, even if a task prompt asks for it implicitly.
10. Any feature touching personal data must be registered in `DataProcessingRecord` and covered by the audit log (Ley 21.719, see `adr/0003-ley-21719-compliance.md`).
11. Do not hardcode data retention periods — they must be configurable (see `adr/0016-configurable-data-retention.md`).
12. Every endpoint serving files must validate ownership (`request.user_id == resource.user_id`) before serving content. Never rely only on the UI for this validation.
13. Authentication is exclusively custom JWT (Access Token + Refresh Token). Do not use Supabase Auth, Cognito, or server-side sessions (see `adr/0004-custom-jwt-authentication.md`).

## MVP Scope

14. Do not implement minor accounts — deferred to v2 (see `adr/0005-minor-accounts-deferred.md`).
15. Do not implement "connected groups" — clubs only exist within a family group in the MVP (see `adr/0006-no-connected-groups-mvp.md`).
16. Do not use Redis in the MVP (see `adr/0012-no-redis-mvp.md`).

## Workflow & Process

17. Read `docs/ai/DEVELOPMENT_WORKFLOW.md` before any implementation task.
18. Never commit or push automatically. Always wait for human approval.
19. Every correctness property defined in a design spec must have at least one corresponding test.
20. The Kiro spec (`.kiro/specs/`) is the single source of truth for implementation. Do not create duplicate spec files elsewhere.

## Conventions

21. Conventional Commits on every commit (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
22. Do not skip or "simplify" an acceptance criterion from a spec without explicitly flagging it as a decision pending human approval.
