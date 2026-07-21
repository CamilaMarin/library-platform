# ADR-0015: Book / Book Copy Separation

## Estado
Aceptado

## Contexto
El modelo de dominio ya distinguía entre `Libro` (metadatos de la obra) y `Ejemplar` (copia poseída por un usuario). Esta ADR formaliza y refuerza esa separación como decisión arquitectónica explícita.

## Decisión
Mantener la separación estricta entre:

- **Book (Libro):** Representa la obra intelectual. Contiene metadatos compartibles (título, autor, géneros, descripción, páginas, ISBN). Puede existir sin que nadie posea una copia.
- **Book Copy (Ejemplar):** Representa una copia poseída. Cada copia tiene exactamente un propietario (`usuario_id`). Puede ser física (solo metadatos + estado) o digital (archivo cifrado aislado).

Relación: Un Book puede tener múltiples Copies. Cada Copy pertenece a exactamente un User.

## Consecuencias
- Este modelo soporta naturalmente: libros físicos, libros digitales, préstamos (sobre copias físicas), bibliotecas compartidas (metadatos de Books visibles al grupo, Copies como detalle de propiedad).
- Los préstamos referencian un `Copy`, no un `Book`.
- El sorteo cruza Books × Copies × participantes para determinar disponibilidad.
- La eliminación de un Book solo es posible si no tiene Copies asociadas (o se eliminan en cascada las del usuario que lo solicita).
