# Business Rules — EntreLíneas

Invariantes de dominio, independientes de la tecnología. Cada regla referencia el spec de origen y su estado en el MVP.

## Reglas activas en MVP

1. Un `Ejemplar` de tipo `digital` nunca puede exponer su `archivo_ref` a un `usuario_id` distinto de su propietario. _(specs/library.md, adr/0001, adr/0009)_
2. Un `Préstamo` solo puede crearse sobre un `Ejemplar` de tipo `físico`. _(specs/loans.md)_
3. Un `TurnoLectura` no puede activarse para un miembro que no posea su propio `Ejemplar` (físico o digital) del libro. _(specs/clubs.md, specs/loans.md)_
4. Ningún dato personal puede tratarse sin un `ConsentimientoDatos` vigente asociado al usuario. _(specs/privacy.md)_
5. Ningún miembro puede ser agregado a un `GrupoFamiliar` sin invitación aceptada explícitamente. _(specs/authentication.md)_
6. La visibilidad de una `Reseña` es siempre decisión explícita de su autor: `private` o `shared` con destino específico (grupo o club). _(specs/privacy.md, adr/0007)_
7. Toda cancelación de cuenta debe purgar archivos digitales asociados y anonimizar logs de auditoría más allá del mínimo legal de retención (configurable). _(specs/privacy.md, adr/0016)_
8. En el sorteo de lectura, un libro solo puede ser candidato si cada participante seleccionado tiene acceso autorizado: copia física disponible o copia digital propia. _(specs/reading-selection.md, adr/0008)_
9. El lector integrado solo puede abrir archivos donde `ejemplar.usuario_id == usuario_autenticado.id`. _(adr/0014, adr/0009)_
10. Los periodos de retención de datos no se hardcodean — deben ser configurables y documentados. _(adr/0016)_
11. Toda dependencia de infraestructura se accede a través de abstracciones — el dominio nunca importa implementaciones concretas. _(adr/0017)_

## Reglas diferidas a v2

12. Toda cuenta de un menor de edad debe estar administrada por un adulto responsable del mismo `GrupoFamiliar`. _(specs/authentication.md, adr/0005 — diferida a v2)_

## Reglas eliminadas del MVP

13. ~~Clubes pueden existir entre grupos conectados explícitamente.~~ — Eliminada. En el MVP, clubes solo dentro de un grupo familiar. _(adr/0006)_
