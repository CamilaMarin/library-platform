---
inclusion: always
---

# Specification Governance — EntreLíneas

## Source of truth hierarchy

1. **ADRs** (`docs/adr/`) are the source of truth for architectural decisions.
2. **Kiro specifications** (`.kiro/specs/`) are the source of truth for implementation.
3. **`docs/PROJECT_CONTEXT.md`** is the entry point for understanding the project.
4. **`docs/steering-rules.md`** documents the rules in prose form; `.kiro/steering/` is what gets auto-loaded.

## Rules

- Never invent functionality outside the approved scope defined in the specifications.
- Never simplify or skip an acceptance criterion from a spec without flagging it explicitly as a decision pending human approval.
- Do not create duplicate specification files in `docs/specs/` for modules that already have Kiro specs. The Kiro spec is the implementation source of truth.
- If implementation reveals a case not contemplated by the spec, update the spec documentation (with approval) — do not silently implement undocumented behavior.

## Specification structure per module

```
.kiro/specs/<module>/
  requirements.md   — What to build (acceptance criteria)
  design.md         — How to build it (architecture, data models, correctness properties)
  tasks.md          — Implementation plan (ordered tasks with DAG)
```

## Correctness properties format

Each property in design.md follows:
```
### Property N: <name>
<description>
**Validates: Requirements X.Y**
```

## Task dependency graph format

Tasks use JSON wave format:
```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2, 3] }
  ]
}
```
