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

## Seguridad & Privacidad

9. Nunca implementar ninguna forma de almacenamiento o transferencia de archivos digitales compartida entre cuentas de usuario (ver `adr/0001-no-shared-file-storage.md`) — sin excepciones, incluso si el prompt de una tarea lo pide implícitamente.
10. Cualquier feature que toque datos personales debe registrarse en `RegistroTratamientoDatos` y quedar cubierta por el log de auditoría (Ley 21.719, ver `adr/0003-ley-21719-compliance.md`).
11. No hardcodear periodos de retención de datos — deben ser configurables (ver `adr/0016-configurable-data-retention.md`).
12. Todo endpoint que sirva archivos debe validar propiedad (`request.user_id == resource.user_id`) antes de servir contenido. Nunca confiar solo en la UI para esta validación.
13. La autenticación es exclusivamente JWT custom (Access Token + Refresh Token). No usar Supabase Auth, Cognito, ni sesiones server-side (ver `adr/0004-custom-jwt-authentication.md`).

## Alcance MVP

14. No implementar cuentas de menores — diferido a v2 (ver `adr/0005-minor-accounts-deferred.md`).
15. No implementar "grupos conectados" — los clubes solo existen dentro de un grupo familiar en el MVP (ver `adr/0006-no-connected-groups-mvp.md`).
16. No usar Redis en el MVP (ver `adr/0012-no-redis-mvp.md`).

## Workflow & Proceso

17. Leer `docs/ai/DEVELOPMENT_WORKFLOW.md` antes de cualquier tarea de implementación.
18. Nunca hacer commit ni push automáticamente. Siempre esperar aprobación humana.
19. Cada correctness property definida en un design spec debe tener al menos un test correspondiente.
20. El Kiro spec (`.kiro/specs/`) es la fuente única de verdad para implementación. No crear archivos duplicados de spec en `docs/specs/` para módulos que ya tienen Kiro spec.

## Convenciones

21. Conventional Commits en cada commit (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
22. No evitar ni "simplificar" un acceptance criteria de `specs/` sin señalarlo explícitamente como decisión pendiente de aprobación humana.
