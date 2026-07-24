# EntreLíneas Development Workflow

## General Philosophy

Work in small, reviewable increments.

Never generate large amounts of code without approval.

Every task must be traceable from:

Requirement
→ Specification
→ Implementation
→ Tests
→ Documentation
→ Commit

---

## Before Starting Any Task

Always:

1. Read PROJECT_CONTEXT.md.
2. Read all approved ADRs related to the module.
3. Read the module specification.
4. Detect ambiguities.
5. Stop if clarification is required.

---

## During Development

Follow:

- Clean Architecture
- SOLID
- Privacy by Design
- Cloud Agnostic principles

Never violate an approved ADR.

---

## Architecture Freeze

The approved architecture is considered frozen.

During implementation:

- Do not introduce new architecture.
- Do not replace approved technologies.
- Do not expand the MVP scope.

If implementation reveals an architectural problem:

1. Stop.
2. Explain the issue.
3. Propose a new ADR.
4. Wait for approval.

Never silently change the approved architecture.

---

## After Completing a Task

Always:

- Update documentation.
- Update IMPLEMENTATION_STATUS.md if progress changed.
- Update CHANGELOG.md if user-visible behavior changed.
- Update API documentation if required.
- Update architecture documentation if affected.
- Update ADR references if applicable.
- Synchronize affected specifications if necessary.
- Verify tests.
- Summarize changes.

Do not commit yet.

---

## Commit Workflow

A commit represents a single logical unit of completed work.

Before proposing a commit:

1. Verify that all related tasks are complete.
2. Verify that all tests pass.
3. Verify that documentation is synchronized.
4. Verify that the implementation complies with all approved ADRs.
5. Verify that the affected specifications remain synchronized.
6. Verify that the Definition of Done has been satisfied.

If any verification fails:

- Stop.
- Explain the issue.
- Do not generate a commit.

---

When the work is ready:

Generate:

- Summary of changes
- Files modified
- Related milestone
- Related specification(s)
- Related ADR(s)
- Implemented task(s)
- Suggested Conventional Commit
- Suggested Pull Request title
- Suggested Pull Request description

Suggested commit format:

<type>(<scope>): <short description>

Body:

- Summary of implementation
- Important design decisions
- Breaking changes (if any)

References:

- ADR: ADR-XXXX
- Spec: <module>
- Tasks:
  - <module>/tasks.md#N
  - <module>/tasks.md#N

---

If unrelated changes are detected:

- Recommend splitting the work into multiple commits.

Never commit automatically.

Never push automatically.

Never rewrite Git history.

Always wait for explicit approval before creating or recommending the next commit.

---

## Git Branching Strategy

All implementation work happens on feature branches. Never commit directly to main/master.

### Branch naming convention

```
feat/<milestone>-<short-description>
fix/<short-description>
docs/<short-description>
refactor/<short-description>
```

Examples:
- `feat/m1-auth-registration-login-refresh`
- `feat/m1-auth-logout-family-groups`
- `fix/refresh-token-timezone`

### Rules

- NEVER commit directly to main/master.
- ALWAYS create a feature branch from the latest main before starting work.
- Use Conventional Commit prefix in branch name (`feat/`, `fix/`, `docs/`, `refactor/`).
- Include the milestone identifier when applicable (e.g., `m1-`, `m2-`).
- One PR per logical unit of work (can contain multiple related tasks from the same wave).
- After PR is merged, create a NEW branch from updated main for the next unit of work.
- Delete merged feature branches (locally and remotely).

### Workflow

1. Before starting: `git checkout main && git pull origin main`
2. Create branch: `git checkout -b feat/<milestone>-<description>`
3. Work, commit, verify.
4. Push: `git push -u origin feat/<milestone>-<description>`
5. Create PR from GitHub.
6. After merge: start again from step 1 for the next task.

Never reuse a merged branch for new work.

---

## Milestone Workflow

Before starting a milestone:

1. Review all related ADRs.
2. Review all related specifications.
3. Review dependencies.
4. Produce an implementation plan.
5. Wait for approval.

When completing a milestone:

1. Verify the Definition of Done.
2. Update IMPLEMENTATION_STATUS.md.
3. Update CHANGELOG.md.
4. Update README progress (if applicable).
5. Update diagrams if architecture changed.
6. Review open risks.
7. Generate a milestone summary.
8. Wait for approval before starting the next milestone.

---

## Definition of Done

A task is considered complete only if all of the following conditions are satisfied:

### Functional

✓ All assigned requirements have been fully implemented.

✓ The implementation matches the approved specification.

✓ No unresolved ambiguity remains.

### Quality

✓ All required tests have been implemented.

✓ All tests pass successfully.

✓ No known regressions have been introduced.

### Documentation

✓ Documentation has been updated and synchronized.

✓ API documentation has been updated if applicable.

✓ IMPLEMENTATION_STATUS.md has been updated if progress changed.

✓ CHANGELOG.md has been updated if user-visible behavior changed.

### Architecture

✓ The implementation complies with all approved ADRs.

✓ The approved architecture has been preserved.

✓ No architectural changes have been introduced without an approved ADR.

### Review

✓ The implementation is ready for review.

✓ A commit proposal has been generated following the Commit Workflow.

Only then request commit approval.

A task is not considered complete until every applicable item in this checklist has been verified.

## Milestone Completion

A milestone is complete only if:

✓ All milestone tasks satisfy the Definition of Done.

✓ All documentation is synchronized.

✓ IMPLEMENTATION_STATUS.md has been updated.

✓ Open risks have been reviewed.

✓ The milestone summary has been generated.

✓ The project is ready to begin the next milestone.

Only then request milestone approval.