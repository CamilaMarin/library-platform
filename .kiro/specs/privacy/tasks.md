# Implementation Plan: Privacy & Ley 21.719 Compliance

## Overview

Implements the cross-cutting privacy infrastructure: consent, processing record, audit log, ARCO rights, configurable retention, and breach notification. Every other module's use cases call into this one.

## Tasks

- [x] 1. `DataConsent` and `DataProcessingRecord` domain models + write-path middleware invoked on every personal-data write _(Req 1.1)_
- [x] 2. `AuditLog` service, invoked transversally by all bounded contexts on create/read/update/delete of personal data _(Req 1.5)_
- [x] 3. `ExerciseARCORight` use case: export, rectify, cancel, oppose _(Req 1.2)_
- [x] 4. Deletion job triggered by cancellation: purges digital files, anonymizes audit logs beyond minimum legal retention _(Req 1.2, 1.7)_
- [x] 5. Data minimization review: audit every model field against "is this strictly necessary?" _(Req 1.4)_
- [x] 6. Encryption at rest and in transit for personal data fields and digital files _(Req 1.6)_
- [x] 7. `RetentionPolicy` entity + configurable retention job: flag and delete data for inactive/closed accounts per configured policy. Users notified before deletion. Duration from database/config, never hardcoded. _(Req 1.7, adr/0016)_
- [x] 8. Breach notification playbook (documented + partially automated) _(Req 1.3)_
- [x] 9. Visibility check enforced at the application layer before any cross-user data read _(Req 1.8)_
- [~] 10. External legal review of the consent flow and processing record before any launch with real user data

## Task Dependency Graph
```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2, 5] },
    { "wave": 3, "tasks": [3, 6, 9] },
    { "wave": 4, "tasks": [4, 7] },
    { "wave": 5, "tasks": [8] },
    { "wave": 6, "tasks": [10] }
  ]
}
```

## Notes

- Task 2 (audit log) must be wired into every other module's use cases (`authentication`, `library`, `clubs`, `loans`, `reviews`, `reading-selection`) — track as a cross-cutting integration checklist.
- Task 3 (ARCO) is the single implementation — `authentication` module integrates with it, not re-implements it.
- Task 7 explicitly references `adr/0016-configurable-data-retention.md` — retention periods are never code constants.
- Task 10 is not an engineering task; treat it as a hard gate before any real user data is processed.
