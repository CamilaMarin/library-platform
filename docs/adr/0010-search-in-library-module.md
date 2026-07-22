# ADR-0010: Search is Part of the Library Module

## Status
Accepted

## Context
The roadmap lists "basic search" as an MVP feature. It was evaluated whether it should be an independent module or part of an existing bounded context.

## Decision
- Search is part of the **Library** module (bounded context Library).
- It is not an independent module or bounded context.

## Consequences
- Search use cases (`SearchBooks`) live in `library/application/`.
- No separate `search/` directory is created in the folder structure.
- If in the future search grows in complexity (full-text, Elasticsearch), it can be extracted to its own infrastructure while maintaining the interface in the Library module.
