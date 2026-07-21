# ADR-0013: Reading Selection as Dedicated Specification

## Estado
Aceptado

## Contexto
La selección de lectura (sorteo aleatorio filtrable, modo de elección por turno) es una funcionalidad core del MVP que diferencia a EntreLíneas de sus competidores. Estaba brevemente descrita dentro de `specs/library.md` pero merece un tratamiento independiente dada su complejidad (filtros, validación de disponibilidad, múltiples modos de selección).

## Decisión
- Crear una especificación dedicada para Reading Selection: `specs/reading-selection.md`.
- Se creará un spec completo en `.kiro/specs/reading-selection/` con requirements, design y tasks.

## Consecuencias
- Los acceptance criteria de selección de lectura se mueven de `specs/library.md` a `specs/reading-selection.md`.
- `specs/library.md` se enfoca exclusivamente en gestión de biblioteca (CRUD de libros y ejemplares, búsqueda, import).
- El bounded context sigue siendo Biblioteca (la selección usa entidades de Library), pero tiene su propia especificación funcional.
