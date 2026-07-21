# ADR-0006: Connected Groups Removed from MVP

## Estado
Aceptado

## Contexto
El spec de clubes mencionaba la posibilidad de crear clubes "entre grupos conectados explícitamente". Este concepto no estaba definido (sin entidad, sin casos de uso, sin spec) e introduce complejidad en el modelo de permisos y visibilidad.

## Decisión
- El concepto de "grupos conectados" se elimina del MVP.
- La única jerarquía social en el MVP es: **Usuario → Grupo → Biblioteca compartida**.
- Los clubes solo pueden existir dentro de un grupo familiar, no entre grupos distintos.

## Consecuencias
- Se simplifica el modelo de permisos: la visibilidad se resuelve siempre dentro del contexto de un grupo.
- Los clubes quedan limitados a miembros del mismo grupo familiar.
- Si en el futuro se desea extender clubes más allá de un grupo, se diseñará el modelo de "conexión entre grupos" como feature separada (requiere revisión de product-principles.md).
