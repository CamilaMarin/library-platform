# ADR-0001: No almacenar ni transferir archivos con copyright entre cuentas

## Estado
Aceptado

## Contexto
El proyecto necesita permitir que los usuarios administren libros digitales (EPUB/PDF) propios y coordinen lectura conjunta en clubes familiares. Existe riesgo legal real: compartir el acceso digital a un archivo con copyright entre distintas personas constituye, en general, infracción de derechos de reproducción/distribución — incluso el modelo de "préstamo digital controlado" (un ejemplar digital por cada ejemplar físico poseído) fue considerado infracción por la Corte de Apelaciones del Segundo Circuito de EE.UU. en *Hachette v. Internet Archive* (2024).

## Decisión
- Cada archivo digital subido por un usuario queda aislado a esa cuenta, cifrado, sin mecanismo de transferencia ni acceso concurrente por parte de otra cuenta, bajo ninguna circunstancia.
- Los "préstamos" solo aplican a ejemplares físicos (registro social/logístico, sin archivo involucrado).
- La coordinación de lectura conjunta de un libro digital se resuelve con el concepto de "turno de lectura", que exige que cada participante posea su propio ejemplar.

## Consecuencias
- Se renuncia a una función atractiva a primera vista ("prestar mi epub a mi hermana") a cambio de evitar exposición legal.
- El modelo se alinea con Calibre/Komga/Kavita (biblioteca personal aislada), no con un sistema de préstamo tipo biblioteca pública.
- Refuerza el principio de producto "el usuario siempre es dueño de su biblioteca".
