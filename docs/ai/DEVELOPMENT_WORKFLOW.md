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

## After Completing a Task

Always:

- Update documentation.
- Update API documentation if required.
- Update architecture documentation if affected.
- Update ADR references if applicable.
- Verify tests.
- Summarize changes.

Do not commit yet.

---

## Commit Workflow

When a logical unit of work is complete:

Generate:

- Summary of changes
- Files modified
- Suggested Conventional Commit
- Suggested Pull Request title
- Suggested Pull Request description

Wait for approval.

Never commit automatically.

Never push automatically.

Never rewrite Git history.

---

## Definition of Done

A task is complete only if:

✓ Requirements implemented

✓ Tests passing

✓ Documentation synchronized

✓ Architecture preserved

✓ No unresolved ambiguity

✓ Ready for review

Only then request commit approval.