# ADR-0012: Redis Removed from MVP

## Estado
Aceptado

## Contexto
El stack original incluía Redis como dependencia "v1+" para sesiones, cache de sorteos y rate limiting. Con la decisión de usar JWT (ADR-0004), el principal motivador de Redis en el MVP (sesiones) desaparece.

## Decisión
- Redis se elimina del MVP.
- La autenticación JWT no requiere almacenamiento de sesiones server-side.
- Redis podrá introducirse en versiones futuras para cache, rate limiting, o funcionalidades que lo justifiquen.

## Consecuencias
- Se reduce la complejidad del docker-compose de desarrollo (menos servicios).
- El rate limiting en el MVP se implementa en memoria o con soluciones ligeras (middleware stateless).
- Si se necesita revocación de tokens JWT antes de su expiración, se evaluará una lista negra en PostgreSQL antes de introducir Redis.
