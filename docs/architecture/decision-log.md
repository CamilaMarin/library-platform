# Decision Log — EntreLíneas

Non-ADR decisions that don't warrant a full Architecture Decision Record but should be tracked for traceability.

For architectural decisions, see `docs/adr/`. This log captures smaller design choices, trade-offs, and implementation decisions.

## Format

| Date | Decision | Reason | Alternatives | Impact | Related ADR | Related Spec | Milestone |
|------|----------|--------|-------------|--------|-------------|-------------|-----------|
| — | — | — | — | — | — | — | — |

## Entries

| Date | Decision | Reason | Alternatives | Impact | Related ADR | Related Spec | Milestone |
|------|----------|--------|-------------|--------|-------------|-------------|-----------|
| 2026-07-26 | Frontend state managed with React Context only (no Redux/Zustand) | App is session-scoped, each page fetches its own data; no cross-page shared state complex enough to justify a library | Redux, Zustand, Jotai | Low — easily reversible if state complexity grows | ADR-0002 | frontend-catchup | M6.5 |
| 2026-07-26 | JWT tokens stored in localStorage | Simplest approach for MVP; works across refreshes; backend already validates tokens server-side | httpOnly cookies (requires BFF/proxy), in-memory only (lost on refresh) | Medium — acceptable for MVP, may migrate to httpOnly cookies for production hardening | ADR-0004, ADR-0012 | frontend-catchup | M6.5 |
| 2026-07-26 | Plain fetch wrapper instead of axios or external HTTP client | Zero additional dependencies; typed wrapper gives same DX; aligns with "no new deps beyond approved stack" principle | axios, ky, ofetch | Low — internal to api-client module, swappable | ADR-0002 | frontend-catchup | M6.5 |
| 2026-07-26 | Client Components as default for API-interactive pages; Server Components only for static shells | Pages need auth state + API calls which require client-side execution; SSR adds complexity without clear benefit for an authenticated SPA | Full SSR with server actions, hybrid RSC data fetching | Low — can adopt more RSC patterns incrementally as Next.js patterns mature | ADR-0002 | frontend-catchup | M6.5 |
| 2026-07-27 | Application-level encryption at rest deferred to post-MVP | No real user data before legal review gate (Task 10); infrastructure-level encryption sufficient for pre-launch; key management complexity disproportionate for MVP | Implement now, infrastructure-only permanent, partial (files only) | Medium — must revisit before Dec 2026 enforcement; retrofitting requires migration if legal review demands field-level encryption | ADR-0018 | privacy | M8 |
| 2026-07-31 | Bookmarks and notes endpoints deferred to v1 (reader-extras) | Reduce initial reader scope to core flow (file serving + progress tracking); bookmarks/notes add complexity without blocking primary reading UX | Ship all reader endpoints now; ship bookmarks only and defer notes | Low — no existing consumers; can be added without breaking changes when reader-extras phase starts | ADR-0014 | library (integrated reader) | v1-reader-extras |
