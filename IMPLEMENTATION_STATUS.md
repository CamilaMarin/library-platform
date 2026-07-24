# Implementation Status — EntreLíneas

Last updated: 2025-07-22

## Overall Progress

- Current milestone: **M1 (Authentication)**
- Milestones completed: **3/11**
- Architecture frozen: **Yes**
- Implementation started: **Yes**

## Milestones

| # | Milestone | Status | Tasks | Completed |
|---|-----------|--------|-------|-----------|
| M-1 | Architecture Validation | ✅ Complete | 7 | 7/7 |
| M0 | Privacy Foundation | ✅ Complete | 3 | 3/3 |
| M1 | Authentication | ✅ Complete | 10 | 10/10 |
| M2 | Users & Groups | Not started | 4 | 0/4 |
| M3 | Library | Not started | 7 | 0/7 |
| M4 | Reading Selection | Not started | 5 | 0/5 |
| M5 | Clubs | Not started | 5 | 0/5 |
| M6 | Reviews | Not started | 5 | 0/5 |
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
- **Status:** Not started
- **Milestone:** M3
- **Spec:** `.kiro/specs/library/`
- **Completed tasks:** 0/7
- **Remaining tasks:** 7
- **Test coverage:** 0%
- **Open issues:** None
- **Blocking issues:** Depends on M2 (User, FamilyGroup)

### Reading Selection (Draw, Pick-by-Turn)
- **Status:** Not started
- **Milestone:** M4
- **Spec:** `.kiro/specs/reading-selection/`
- **Completed tasks:** 0/7
- **Remaining tasks:** 7
- **Test coverage:** 0%
- **Open issues:** None
- **Blocking issues:** Depends on M3 (Book, Copy)

### Community (Clubs, Reading Turns)
- **Status:** Not started
- **Milestone:** M5
- **Spec:** `.kiro/specs/clubs/`
- **Completed tasks:** 0/6
- **Remaining tasks:** 6
- **Test coverage:** 0%
- **Open issues:** None
- **Blocking issues:** Depends on M3 (Copy ownership)

### Reviews
- **Status:** Not started
- **Milestone:** M6
- **Spec:** `.kiro/specs/reviews/`
- **Completed tasks:** 0/6
- **Remaining tasks:** 6
- **Test coverage:** 0%
- **Open issues:** None
- **Blocking issues:** Depends on M5 (Club membership for shared_with)

### Circulation (Loans)
- **Status:** Not started
- **Milestone:** M7
- **Spec:** `.kiro/specs/loans/`
- **Completed tasks:** 0/5
- **Remaining tasks:** 5
- **Test coverage:** 0%
- **Open issues:** None
- **Blocking issues:** Depends on M3 (Copy entity)

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

**M1: Authentication**

Goal: Implement JWT registration/login with consent gating, token rotation, and revocation.

Prerequisites: M0 complete ✅ (DataConsent, AuditLog service available)

Progress:
- ✅ Task 1: Domain entities (User, DataConsent, FamilyGroup, RefreshToken) + migration
- ✅ Task 2: RegisterUser use case + persistence (consent-gating)
- ✅ Task 3: POST /auth/register + POST /auth/consent endpoints
- ✅ Task 4: LoginUser use case + POST /auth/login (JWT issuance)
- ✅ Task 5: RefreshToken use case + POST /auth/refresh (atomic rotation)
- ✅ Task 6: RevokeToken use case + POST /auth/logout
- ✅ Task 7: CreateFamilyGroup use case + POST /groups (+ auth dependency)
- ✅ Task 8: InviteGroupMember / AcceptGroupInvitation
- ✅ Task 9: ARCO integration (GET /users/me/export, DELETE /users/me)
- ✅ Task 10: Domain + integration tests (full coverage — 154 tests)

**Milestone M1 complete — ready for M2.**
