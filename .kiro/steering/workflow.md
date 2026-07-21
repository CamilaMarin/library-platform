---
inclusion: always
---

# Development Workflow Rules — EntreLíneas

## Before any implementation task

1. Read `docs/PROJECT_CONTEXT.md`.
2. Read `docs/ai/DEVELOPMENT_WORKFLOW.md`.
3. Read all approved ADRs related to the module.
4. Read the module's Kiro specification (`.kiro/specs/<module>/`).
5. Detect ambiguities — stop and ask if clarification is needed.

## During development

- Work in small, reviewable increments.
- Never generate large amounts of code without approval.
- Follow Clean Architecture, SOLID, Privacy by Design, Cloud Agnostic principles.
- Never violate an approved ADR.

## Commit and approval rules

- NEVER commit automatically.
- NEVER push automatically.
- NEVER rewrite git history.
- At every logical milestone, generate:
  - Summary of changes
  - Files modified
  - Suggested Conventional Commit message
  - Suggested PR title and description
- WAIT for human approval before proceeding.

## After completing a task

- Update documentation if affected.
- Update API documentation if endpoints changed.
- Verify tests pass.
- Summarize changes.
- Request approval.

## Definition of Done

A task is complete only if:
- ✓ Requirements implemented
- ✓ Tests passing
- ✓ Documentation synchronized
- ✓ Architecture preserved
- ✓ No unresolved ambiguity
- ✓ Ready for review

Full workflow details: `docs/ai/DEVELOPMENT_WORKFLOW.md`
