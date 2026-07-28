# Implementation Status — EntreLíneas

Last updated: 2025-07-27

## Overall Progress

- Current milestone: **M9 (Release Candidate)**
- Milestones completed: **11/12**
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
| M6.5 | Frontend Catchup | ✅ Complete | 24 | 24/24 |
| M7 | Loans | ✅ Complete | 5 | 5/5 |
| M8 | Privacy Panel | ✅ Complete | 10 | 10/10 |
| M9 | Release Candidate | In progress | 10 | 1/10 |

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
- **REST endpoints:** 8 endpoints (list, create, detail, members, comments, active-book, available-books)
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
- **Status:** Complete
- **Milestone:** M7
- **Spec:** `.kiro/specs/loans/`, `.kiro/specs/loans-frontend/`
- **Completed tasks:** 5/5 (backend) + 10/10 (frontend)
- **Remaining tasks:** 0
- **Test coverage:** 16 backend tests (7 domain + 5 integration + 4 regression) + 24 frontend tests
- **Frontend pages:** `/loans` (active/returned tabs), library loan integration (copy status badges, "Prestar" button, inline LoanForm)
- **Open issues:** None
- **Blocking issues:** None

### Frontend (UI Catchup)
- **Status:** Complete
- **Milestone:** M6.5
- **Spec:** `.kiro/specs/frontend-catchup/`
- **Completed tasks:** 24/24
- **Remaining tasks:** 0
- **Test coverage:** 24 tests passing (7 toast + 9 auth context + 5 API client PBTs + 3 ProtectedRoute PBTs)
- **Pages delivered:**
  - Login (`/login`) — email/password with error mapping
  - Register (`/register`) — consent-gated, field validation
  - Dashboard (`/dashboard`) — book count summary, navigation grid
  - Library (`/library`) — search, pagination, add book, add copy
  - Groups (`/groups`) — create, invite, accept/decline invitations, member list
  - Selection (`/selection`) — per-group draw trigger with filters, history, next picker
  - Clubs (`/clubs`) — list, create club
  - Club Detail (`/clubs/[id]`) — active book, comments with spoiler toggle, members
  - Reviews (`/reviews`) — create/edit/delete, star rating, privacy-first visibility
  - Settings (`/settings`) — ARCO data export, account deletion with email confirmation
- **Infrastructure:**
  - API client (Bearer token, 401 refresh/retry, error propagation, toast integration)
  - Token storage (localStorage, JWT decode)
  - Auth context (login, register, logout, session persistence)
  - Toast system (auto-dismiss, stacked, responsive)
  - ProtectedRoute (redirect preservation)
  - Navigation (desktop sidebar + mobile bottom bar)
  - Shared components (InputField, SelectField, StarRating, ConfirmDialog, Skeleton)
  - Testing infra (Vitest, React Testing Library, MSW, fast-check)
- **Open issues:** None
- **Blocking issues:** None

### Privacy (Foundation + Panel)
- **Status:** Complete
- **Milestone:** M0, M8
- **Spec:** `.kiro/specs/privacy/`
- **Completed tasks:** 10/10
- **Remaining tasks:** 0
- **Test coverage:** 10 domain tests (M0) + 15 ARCO tests + 10 purge tests + 11 encryption tests + 11 retention tests
- **Implemented:**
  - DataConsent, DataProcessingRecord, AuditLog entities + repositories (M0)
  - RetentionPolicy entity with configurable retention job (ADR-0016)
  - ARCO rights: Export (Access), RectifyUserData (Rectification), DeleteUserAccount (Cancellation), OpposeDataProcessing (Opposition)
  - PurgeUserData: cross-cutting data cleanup (digital files, copies, reviews, loans, audit anonymization)
  - FieldEncryptor: Fernet symmetric encryption for PII fields
  - Retention job: configurable policy enforcement via DB (POST /admin/retention/run + CLI script)
  - Data minimization audit document
  - Breach notification playbook (Ley 21.719 Art. 14 bis)
  - Visibility checks enforced across all modules
- **Open issues:** None
- **Blocking issues:** None

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
| Application-level encryption at rest | Key management complexity; infrastructure-level encryption sufficient pre-launch; gated by legal review (ADR-0018) | Was M8 (Task 6) |

## Next Milestone

**M9: Release Candidate**

Goal: Final integration testing, performance validation, deployment preparation, and release readiness.

Prerequisites: M8 complete ✅ (All privacy compliance in place)
