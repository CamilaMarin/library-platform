# Steering Rules — EntreLíneas

> Reglas permanentes para cualquier agente de IA (Kiro, Claude Code, etc.) que implemente sobre este proyecto. Se cargan siempre junto a `PROJECT_CONTEXT.md`, sin importar el módulo de la tarea.

## Arquitectura & Código

1. Seguir Clean Architecture: el domain layer nunca importa framework ni infraestructura.
2. Toda lógica de negocio vive en el dominio, no en controladores ni en la capa de infraestructura.
3. Nunca acceder directamente a la base de datos desde los controladores — siempre a través de un caso de uso.
4. Usar Dependency Injection para toda dependencia externa.
5. Toda dependencia de infraestructura se accede a través de abstracciones (interfaces/protocolos). El proyecto es cloud agnostic — ver `adr/0017-cloud-agnostic-abstractions.md`.
6. Toda funcionalidad nueva requiere tests (dominio + integración) antes de darse por terminada.
7. No agregar librerías nuevas sin justificar por qué lo ya disponible no alcanza.
8. Priorizar claridad sobre optimización prematura.

## Restricciones de negocio

9. Nunca implementar ninguna forma de almacenamiento o transferencia de archivos digitales compartida entre cuentas de usuario (ver `adr/0001-no-shared-file-storage.md`) — sin excepciones, incluso si el prompt de una tarea lo pide implícitamente.
10. Cualquier feature que toque datos personales debe registrarse en `RegistroTratamientoDatos` y quedar cubierta por el log de auditoría (Ley 21.719, ver `adr/0003-ley-21719-compliance.md`).
11. No hardcodear periodos de retención de datos — deben ser configurables (ver `adr/0016-configurable-data-retention.md`).
12. El lector integrado solo puede abrir archivos cuyo `ejemplar.usuario_id == request.user_id` (ver `adr/0014-integrated-reader-mvp.md`).

## Modelo de datos

13. Respetar la separación Book (obra intelectual) vs. Copy (ejemplar poseído). Ver `adr/0015-book-copy-separation.md`.
14. Reseñas usan modelo `visibility` (private|shared) + `shared_with` (destino explícito). Ver `adr/0007-review-visibility-model.md`.

## Alcance MVP

15. No implementar cuentas de menores — diferido a v2 (ver `adr/0005-minor-accounts-deferred.md`).
16. No implementar "grupos conectados" — los clubes solo existen dentro de un grupo familiar en el MVP (ver `adr/0006-no-connected-groups-mvp.md`).
17. No usar Redis en el MVP (ver `adr/0012-no-redis-mvp.md`).
18. Search e Import son parte de Library, no módulos independientes (ver `adr/0010`, `adr/0011`).

## Convenciones

19. Conventional Commits en cada commit (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
20. No evitar ni "simplificar" un acceptance criteria de `specs/` sin señalarlo explícitamente como decisión pendiente de aprobación humana.
