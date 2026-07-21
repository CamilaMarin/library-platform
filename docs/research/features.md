# Research — Feature Backlog

Backlog clasificado por versión. Categorías base tomadas de la sesión de brainstorming y ajustadas a los principios del producto (círculo cerrado, sin compartir archivos, privacy by design).

## MVP (Fase 1)

- **Books / Library**: alta de libros (metadatos de la obra), ejemplares físicos y digitales (modelo Book/Copy separado), edición y borrado. Búsqueda e import como casos de uso de Library (ver `adr/0010`, `adr/0011`).
- **Integrated Reader**: lector EPUB/PDF integrado, progreso de lectura, marcadores y notas. Solo archivos propios (ver `adr/0014`).
- **Groups**: creación de grupo familiar, invitación con aceptación explícita. Sin distinción adulto/menor en MVP (ver `adr/0005`).
- **Reading Selection**: sorteo filtrable (género, páginas, disponibilidad para todos, no leído), modo "elección por turno". Spec dedicada (ver `adr/0013`). Disponibilidad = acceso autorizado por cada participante (ver `adr/0008`).
- **Clubs**: creación de club dentro de un grupo familiar (no entre grupos en MVP, ver `adr/0006`), libro activo, fecha de discusión, comentarios con marcado de spoiler.
- **Loans**: préstamo de ejemplares físicos, turno de lectura para digitales (sin transferencia de archivo).
- **Reviews**: calificación + opinión, con visibilidad `private | shared` y destino explícito (grupo o club específico, ver `adr/0007`).
- **Privacy**: consentimiento explícito, derechos ARCO self-service, registro de tratamiento, logs de auditoría, retención configurable (ver `adr/0016`).
- **Authentication**: JWT custom con Access Token + Refresh Token (ver `adr/0004`). Sin Redis (ver `adr/0012`).
- **Search**: búsqueda básica dentro de la biblioteca propia y del grupo (solo metadatos). Parte de Library.
- **Import**: alta manual + autocompletado de metadatos (ISBN/título vía fuente pública tipo Open Library). Parte de Library.

## v1 (Fase 2)

- **Bookmarks / Highlights / Notes avanzados**: funcionalidades extendidas del lector.
- **Reading Sessions**: registro de sesiones de lectura (tiempo, páginas), base para estadísticas.
- **Goals**: metas de lectura personales o de grupo (ej. "leer 12 libros este año").
- **Statistics**: páginas leídas, libros por género, ritmo de lectura.
- **Export**: exportación general de datos más allá de lo mínimo ARCO (ej. backup completo en JSON).
- **Notifications**: recordatorios de club, devolución de préstamos, turnos de lectura.
- **Redis**: cache, rate limiting, funcionalidades que lo justifiquen.

## v2 (Fase 3)

- **Authors / Series / Publishers / Collections**: enriquecimiento del catálogo de metadatos, listas temáticas.
- **Minor accounts**: cuentas de menores con adulto responsable, permisos diferenciados (ver `adr/0005`).
- **Connected groups**: potencialmente extender clubes más allá de un grupo familiar (requiere diseño previo, ver `adr/0006`).
- **Challenges**: retos de lectura grupales con progreso compartido.
- **Achievements**: logros/insignias por hitos de lectura (opcional, cuidando no convertir la app en gamificación distractora).

## Futuro (sin comprometer fecha)

- **Recommendations**: motor de recomendación, potencialmente con IA, basado en historial propio y del grupo.
- **Friends / grupos conectados ampliados**: extender más allá del núcleo familiar manteniendo el modelo de círculo cerrado (nunca red pública). Requiere revisión de `product-principles.md` antes de implementarse.

## Explícitamente descartado

- Feed público / descubrimiento social abierto.
- Cualquier forma de compartir o transferir el archivo digital entre cuentas (ver `adr/0001-no-shared-file-storage.md`).
