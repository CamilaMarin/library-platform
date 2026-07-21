# Spec — Reading Selection (Sorteo de Lectura)

> Spec dedicada por la complejidad de esta feature core. Ver `adr/0013-reading-selection-dedicated-spec.md`.

## Requirement: Sorteo aleatorio filtrable

**User Story:** Como miembro de un grupo familiar, quiero que el sistema nos ayude a elegir qué leer juntos, de forma justa y filtrable.

### Acceptance Criteria
1. EL SISTEMA DEBERÁ ofrecer un sorteo aleatorio filtrable por: género, páginas máximas, disponibilidad para todos los participantes, y libros no leídos por el grupo.
2. CUANDO se ejecuta un sorteo, EL SISTEMA DEBERÁ mostrar de qué biblioteca proviene cada candidato, sin exponer archivos.
3. La regla de "disponibilidad para todos" significa: cada participante seleccionado debe tener acceso autorizado al libro elegido (ver `adr/0008-reading-selection-availability.md`):
   - Para libros físicos: debe existir al menos una copia disponible (no prestada) accesible al participante.
   - Para libros digitales: cada participante debe poseer su propia copia personal.

## Requirement: Selección por turno

### Acceptance Criteria
1. EL SISTEMA DEBERÁ ofrecer un modo alternativo de elección por turno entre miembros del grupo (rotación de quién elige el próximo libro).
