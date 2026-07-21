# Spec — Clubs & Reading Turns

## Requirement: Clubes de lectura

**User Story:** Como organizador de un club, quiero coordinar qué se lee, cuándo, y centralizar los comentarios.

### Acceptance Criteria
1. EL SISTEMA DEBERÁ permitir crear clubes dentro de un grupo familiar.
2. EL SISTEMA DEBERÁ permitir asignar un libro activo y una fecha estimada de discusión por club.
3. EL SISTEMA DEBERÁ ofrecer comentarios por libro/club, con marcado opcional de spoiler.
4. EL SISTEMA NO DEBERÁ requerir ni facilitar la transferencia del archivo digital entre miembros del club; cada miembro debe tener su propio ejemplar.

> Nota: En el MVP, los clubes solo pueden existir dentro de un grupo familiar. El concepto de "grupos conectados" fue eliminado del MVP (ver `adr/0006-no-connected-groups-mvp.md`).

## Requirement: Turno de lectura

### Acceptance Criteria
1. EL SISTEMA DEBERÁ coordinar el orden y los comentarios de un libro digital mediante `TurnoLectura`, sin mover el archivo entre cuentas.
2. EL SISTEMA DEBERÁ validar que un usuario posea su propio ejemplar antes de activar su turno.
