# ADR-0011: Import is a Library Use Case

## Status
Accepted

## Context
The roadmap lists "manual import + metadata autocomplete" as an MVP feature. It was evaluated whether it should be an independent bounded context.

## Decision
- Import is a **use case within the Library module**, not an independent bounded context.
- The use case `ImportBookMetadata` (or `AutocompleteMetadata`) lives in `library/application/`.

## Consequences
- No separate `import/` directory is created.
- Integration with external sources (Open Library, Google Books) is implemented as an adapter in `library/infrastructure/`, behind an interface defined in the application layer.
- Maintains cohesion of the Library bounded context.
