# ADR-0008: Reading Selection — Availability Rule

## Estado
Aceptado

## Contexto
El criterio de sorteo "disponibilidad para todos" era ambiguo — no quedaba claro si significaba que todos poseen una copia, que la copia está disponible (no prestada), o ambos.

## Decisión
La regla de "disponibilidad para todos" se define como:

> **Cada participante seleccionado debe tener acceso autorizado al libro elegido.**

- Para **libros físicos**: debe existir al menos una copia disponible (no prestada) accesible al participante.
- Para **libros digitales**: cada participante debe poseer su propia copia personal autorizada.

## Consecuencias
- El algoritmo de sorteo debe cruzar participantes × ejemplares, verificando propiedad/disponibilidad por cada participante.
- Un libro digital solo puede entrar en el sorteo si todos los participantes lo poseen individualmente.
- Un libro físico solo puede entrar si hay suficientes copias disponibles o un mecanismo de turnos aplicable.
- Refuerza ADR-0001: nunca se ofrece acceso al archivo digital de otro usuario como forma de "disponibilidad".
