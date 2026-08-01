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
| 2026-07-31 | ARCO profile panel task 5.2 (Rectification Form submission logic) marked blocked | Task moved from in-progress `[~]` to blocked `[-]`; submission logic depends on task 5.1 page structure being stable and on backend PATCH `/users/me` endpoint being available and tested end-to-end | Keep in-progress and work in parallel, skip entirely | Low — task is self-contained; unblocking requires completing 5.1 and verifying backend endpoint; no downstream tasks blocked by this alone | ADR-0003, ADR-0004 | arco-profile-panel | M8 |
| 2026-08-01 | view-registered-oppositions task 6 (Unit tests for GetUserOppositions) marked blocked | Task moved from in-progress `[~]` to blocked `[-]`; unit tests for the use case depend on the implementation in tasks 3.1–3.5 being stable and the integration test suite (task 7) providing broader coverage first | Keep in-progress, skip entirely, merge into task 7 | Low — unit tests are additive; no downstream tasks are blocked; can be unblocked once tasks 4 and 5 confirm the implementation is stable | — | view-registered-oppositions | M8 |
