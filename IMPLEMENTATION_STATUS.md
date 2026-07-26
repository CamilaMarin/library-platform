# Implementation Status — EntreLíneas

Last updated: 2025-07-24

## Overall Progress

- Current milestone: **M6.5 (Frontend Catchup)** — in progress
- Milestones completed: **8/12**
- Architecture frozen: **Yes**
- Implementation started: **Yes**

## Milestones

| # | Milestone | Status | Tasks | Completed |
|---|-----------|--------|-------|-----------|
| M-1 | Architecture Validation | ✅ Complete | 7 | 7/7 |
| M0 | Privacy Foundation | ✅ Complete | 3 | 3/3 |
| M1 | Authentication | ✅ Complete | 10 | 10/10 |
| M2 | Users & Groups | ✅ Complete | 4 | 4/4 |
| M3 | Library | ✅ Complete | 7 | 6/7 |
| M4 | Reading Selection | ✅ Complete | 5 | 5/5 |
| M5 | Clubs | ✅ Complete | 5 | 5/5 |
| M6 | Reviews | ✅ Complete | 6 | 6/6 |
| M6.5 | Frontend Catchup | 🔄 In Progress | 24 | 11/24 |
| M7 | Loans | Not started | 4 | 0/4 |
| M8 | Privacy Panel | Not started | 7 | 0/7 |
| M9 | Release Candidate | Not started | 10 | 0/10 |

## Modules

### Identity (Authentication, Users, Groups)
- **Status:** Complete
- **Milestone:** M1, M2
- **Spec:** `.kiro/specs/authentication/`
- **Completed tasks:** 10/10
- **Remaining tasks:** 0
- **Test coverage:** 154 tests passing (domain + integration + acceptance)
- **Open issues:** None
- **Blocking issues:** None

### Library (Books, Copies, Search)
- **Status:** Complete
- **Milestone:** M3
- **Spec:** `.kiro/specs/library/`
- **Completed tasks:** 6/7 (task 5 Import deferred to v1)
- **Remaining tasks:** 0 (task 5 deferred)
- **Test coverage:** 26 tests (11 domain + 15 integration)
- **Open issues:** None
- **Blocking issues:** None

### Reading Selection (Draw, Pick-by-Turn)
- **Status:** Complete
- **Milestone:** M4
- **Spec:** `.kiro/specs/reading-selection/`
- **Completed tasks:** 7/7
- **Remaining tasks:** 0
- **Test coverage:** 21 tests (11 domain + 10 integration)
- **Test coverage:** 11 domain tests
- **Open issues:** None
- **Blocking issues:** None

### Community (Clubs, Reading Turns)
- **Status:** Complete
- **Milestone:** M5
- **Spec:** `.kiro/specs/clubs/`
- **Completed tasks:** 6/6
- **Remaining tasks:** 0
- **Test coverage:** 17 tests (8 domain + 9 integration)
- **Open issues:** None
- **Blocking issues:** None

### Reviews
- **Status:** Complete
- **Milestone:** M6
- **Spec:** `.kiro/specs/reviews/`
- **Completed tasks:** 6/6
- **Remaining tasks:** 0
- **Test coverage:** 85 tests (15 domain + 53 use case/integration + 10 comprehensive + 7 privacy)
- **Open issues:** None
- **Blocking issues:** None

### Circulation (Loans)
- **Status:** Not started
- **Milestone:** M7
- **Spec:** `.kiro/specs/loans/`
- **Completed tasks:** 0/5
- **Remaining tasks:** 5
- **Test coverage:** 0%
- **Open issues:** None
- **Blocking issues:** Depends on M3 (Copy entity)

### Frontend (UI Catchup)
- **Status:** In Progress
- **Milestone:** M6.5
- **Spec:** `.kiro/specs/frontend-catchup/`
- **Completed tasks:** 11/24 (required) + 2/11 (optional PBTs)
- **Remaining tasks:** 13 required
- **Test coverage:** 7 toast tests + 9 auth context tests + 5 API client PBTs passing (21 tests total)
- **Completed modules:**
  - TypeScript type definitions (`src/types/index.ts`)
  - Token storage (`src/lib/token-storage.ts`)
  - API client with 401 refresh, error propagation, toast integration (`src/lib/api-client.ts`)
  - Toast context + component (`src/context/toast-context.tsx`, `src/components/toast.tsx`)
  - Auth context with login/register/logout (`src/context/auth-context.tsx`)
  - ProtectedRoute component (`src/components/protected-route.tsx`)
  - Shared form components (InputField, SelectField, StarRating, ConfirmDialog, Skeleton)
  - Navigation component (desktop sidebar + mobile bottom bar)
  - Root layout with providers (`src/app/layout.tsx`, `src/app/providers.tsx`)
  - Root page redirect (`src/app/page.tsx`)
  - Testing infrastructure (Vitest + RTL + MSW + fast-check)
- **Remaining:**
  - Login/Register pages
  - Dashboard page
  - Library page + Add Book/Copy
  - Groups page
  - Reading Selection page
  - Clubs pages (list + detail)
  - Reviews page
  - Settings page
  - Checkpoints (test verification passes)
- **Open issues:** None
- **Blocking issues:** None

### Privacy (Foundation + Panel)
- **Status:** Not started
- **Milestone:** M0, M8
- **Spec:** `.kiro/specs/privacy/`
- **Completed tasks:** 0/10
- **Remaining tasks:** 10
- **Test coverage:** 0%
- **Open issues:** None
- **Blocking issues:** None (M0 has no dependencies)

## Risk Log

| Risk | Status | Milestone | Notes |
|------|--------|-----------|-------|
| Docker networking (Windows/WSL2) | Open | M-1 | Will be validated in Architecture Validation |
| JWT refresh token replay | Mitigated | M1 | Implemented: atomic rotation revokes old token before storing new one (RefreshTokenUseCase) |
| Storage provider encryption | Open | M3 | Using MinIO SSE, no custom crypto |
| Concurrent loan conflicts | Open | M7 | Will use SELECT FOR UPDATE |
| ARCO export completeness | Open | M8 | Each module registers exportable data |
| Specification Drift | Open | All | Pre-milestone review gate |

## Deferred to v1

| Feature | Reason | Original milestone |
|---------|--------|-------------------|
| Integrated Reader (EPUB/PDF) | Highest technical risk | Was M4 |
| Bookmarks & Notes | Reader-dependent | Was M4 |
| Metadata Import (Open Library) | Convenience, no dependency | Was M3 |
| Advanced audit logging | Extensible later | Was M0 |
| Automated retention worker | Operational, not domain | Was M8 |

## Next Milestone

**M6.5: Frontend Catchup** (in progress)

Goal: Deliver complete Next.js 16 frontend covering all backend functionality from M0–M6 (auth, groups, library, selection, clubs, reviews, privacy).

Prerequisites: M6 complete ✅ (all backend endpoints available)

**After M6.5: M7 — Loans**

Goal: Implement book lending between family group members with copy reservation and conflict handling.

Prerequisites: M3 complete ✅ (Copy entity available)
