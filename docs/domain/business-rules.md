# Business Rules — EntreLíneas

Domain invariants, independent of technology. Each rule references its spec origin and MVP status.

## Active MVP Rules

1. A digital Copy's `file_ref` is never exposed to a `user_id` other than its owner. _(adr/0001, adr/0009)_
2. A Loan can only be created for a Copy of type `physical`. _(Loans spec)_
3. A ReadingTurn cannot be activated for a member who doesn't own their own Copy (physical or digital) of the book. _(Clubs spec)_
4. No personal data may be processed without a valid `DataConsent` associated with the user. _(Privacy spec)_
5. No member may be added to a FamilyGroup without an explicitly accepted invitation. _(Authentication spec)_
6. Review visibility is always an explicit choice by the author: `private` or `shared` with a specific target (group or club). _(adr/0007)_
7. Account cancellation must purge associated digital files and anonymize audit logs beyond the minimum legal retention period (configurable). _(Privacy spec, adr/0016)_
8. In the reading draw, a book can only be a candidate if every selected participant has authorized access: available physical copy or personally owned digital copy. _(Reading Selection spec, adr/0008)_
9. The integrated reader can only open files where `copy.user_id == authenticated_user.id`. _(adr/0014, adr/0009)_
10. Data retention periods are never hardcoded — they must be configurable and documented. _(adr/0016)_
11. Every infrastructure dependency is accessed through abstractions — the domain never imports concrete implementations. _(adr/0017)_

## Rules Deferred to v2

12. Every minor's account must be managed by a responsible adult in the same FamilyGroup. _(adr/0005 — deferred to v2)_

## Rules Removed from MVP

13. ~~Clubs can exist across explicitly connected groups.~~ — Removed. In the MVP, clubs only within a family group. _(adr/0006)_
