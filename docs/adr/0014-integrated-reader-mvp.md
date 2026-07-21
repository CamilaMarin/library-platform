# ADR-0014: Integrated EPUB/PDF Reader in MVP

## Estado
Aceptado

## Contexto
Se debatió si el MVP debía incluir un lector integrado o solo gestión de biblioteca (metadatos). Dado que la propuesta de valor incluye "acompañar la lectura", un lector básico refuerza la experiencia y justifica que el usuario suba sus archivos a la plataforma.

## Decisión
- El MVP incluye un **lector integrado de EPUB y PDF**.
- El lector solo abre archivos subidos por el usuario autenticado actual (refuerza ADR-0001 y ADR-0009).
- Se almacenan: progreso de lectura, marcadores (bookmarks) y notas, asociados al usuario y al ejemplar.

## Consecuencias
- Se necesita una librería de renderizado EPUB/PDF en el frontend (ej. epub.js, PDF.js).
- El backend debe servir el archivo cifrado solo al propietario (validación estricta en el endpoint de descarga).
- Se crean entidades adicionales: `ProgresoLectura`, `Marcador`, `Nota` — asociadas a un Ejemplar digital y su propietario.
- Los datos del lector (progreso, notas) son datos personales y quedan cubiertos por Ley 21.719 (registro de tratamiento, exportación ARCO).
