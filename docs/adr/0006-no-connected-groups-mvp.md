# ADR-0006: Connected Groups Removed from MVP

## Status
Accepted

## Context
The clubs spec mentioned the possibility of creating clubs "across explicitly connected groups." This concept was undefined (no entity, no use cases, no spec) and introduces complexity in the permissions and visibility model.

## Decision
- The "connected groups" concept is removed from the MVP.
- The only social hierarchy in the MVP is: **User → Group → Shared Library**.
- Clubs can only exist within a family group, not across different groups.

## Consequences
- Simplifies the permission model: visibility is always resolved within a single group context.
- Clubs are limited to members of the same family group.
- If in the future clubs should extend beyond a group, the "group connection" model will be designed as a separate feature (requires review of product-principles.md).
