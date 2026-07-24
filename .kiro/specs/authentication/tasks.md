# Implementation Plan: Authentication & Groups

## Overview

Implements account registration with consent gating, JWT authentication (access + refresh tokens), and family group creation/invitation. Foundation module — other modules depend on `user_id`/`group_id` from here.

## Tasks

- [x] 1. Domain model: `User`, `DataConsent`, `FamilyGroup`, `RefreshToken` entities (no external dependencies) _(Req 1, 2, 3)_
- [x] 2. `RegisterUser` use case + persistence, blocked until `DataConsent` exists _(Req 1)_
- [x] 3. Endpoints `POST /auth/register` + `POST /auth/consent` _(Req 1)_
- [x] 4. `LoginUser` use case + `POST /auth/login` endpoint with secure password hashing, returns Access Token + Refresh Token _(Req 1.3, 2.1)_
- [x] 5. `RefreshToken` use case + `POST /auth/refresh` endpoint with token rotation _(Req 2.3)_
- [ ] 6. `RevokeToken` use case + `POST /auth/logout` endpoint _(Req 2.4)_
- [ ] 7. `CreateFamilyGroup` use case + `POST /groups` endpoint _(Req 3.1)_
- [ ] 8. `InviteGroupMember` / `AcceptGroupInvitation` use cases + endpoints, validating explicit acceptance _(Req 3.1, 3.2)_
- [ ] 9. Integration with Privacy module's `ExerciseARCORight` for `GET /users/me/export` and `DELETE /users/me` _(Req 4)_
- [ ] 10. Domain + integration tests covering every acceptance criterion in this spec

## Task Dependency Graph
```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2, 7] },
    { "wave": 3, "tasks": [3, 8] },
    { "wave": 4, "tasks": [4] },
    { "wave": 5, "tasks": [5, 6] },
    { "wave": 6, "tasks": [9] },
    { "wave": 7, "tasks": [10] }
  ]
}
```

## Notes

- ARCO rights (export, cancellation) are owned by the Privacy module (see `.kiro/specs/privacy/`). This module integrates with them, not re-implements them.
- Minor account detection (date_of_birth, adult linking) is deferred to v2 per `adr/0005-minor-accounts-deferred.md`.
- Requires Privacy module's audit log service to be available for personal-data operations.
