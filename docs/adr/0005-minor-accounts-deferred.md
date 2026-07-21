# ADR-0005: Minor Accounts Deferred to v2

## Estado
Aceptado

## Contexto
La regla de negocio 5 exige que toda cuenta de un menor esté gestionada por un adulto responsable del mismo grupo familiar. Esto introduce complejidad significativa en el modelo de permisos del MVP (permisos diferenciados, aprobación parental, restricciones de contenido).

## Decisión
- Las cuentas de menores se posponen a la versión 2.
- En el MVP, todos los usuarios comparten el mismo modelo de permisos — no hay distinción adulto/menor.

## Consecuencias
- Se simplifica el flujo de registro y la gestión de grupos familiares en el MVP.
- La regla de negocio 5 (`domain/business-rules.md`) queda vigente pero su implementación se difiere.
- No se requiere `fecha_nacimiento` como campo obligatorio en el registro del MVP (aunque puede capturarse opcionalmente).
- Antes de v2, se deberá diseñar el modelo de permisos diferenciado y la vinculación menor-adulto.
