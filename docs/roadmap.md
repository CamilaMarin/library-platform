# Roadmap — EntreLíneas

Ver detalle completo de cada ítem en `research/features.md`.

## MVP (Fase 1)
Biblioteca personal (físico/digital) con modelo Book/Copy separado · Lector integrado EPUB/PDF (con progreso, marcadores, notas) · Grupo familiar · Selección conjunta de lectura (sorteo filtrable + modo turno) · Clubes básicos (solo dentro de un grupo) · Préstamos físicos + turno de lectura digital · Reseñas con visibilidad configurable (private/shared con destino explícito) · Cumplimiento Ley 21.719 (ARCO, consentimiento, auditoría, retención configurable) · Búsqueda básica (parte de Library) · Import manual + autocompletado de metadatos (parte de Library) · Autenticación JWT custom (Access + Refresh Token).

### Explícitamente diferido del MVP
- Cuentas de menores (diferido a v2, ver `adr/0005`).
- Grupos conectados / clubes entre grupos (eliminado del MVP, ver `adr/0006`).
- Redis (eliminado del MVP, ver `adr/0012`).

## v1 (Fase 2)
Bookmarks / Highlights / Notes avanzados · Reading Sessions · Goals · Statistics · Export general (backup) · Notifications · Redis (cache, rate limiting).

## v2 (Fase 3)
Authors / Series / Publishers / Collections · Challenges · Achievements · **Cuentas de menores** (adulto responsable, permisos diferenciados) · Potencialmente "grupos conectados" (requiere diseño previo).

## Futuro
Recommendations (potencialmente con IA) · Grupos conectados ampliados (revisando siempre el principio de círculo cerrado antes de abrir alcance).

## Explícitamente fuera de alcance permanente
Feed público / descubrimiento social abierto · Transferencia de archivos digitales entre cuentas bajo cualquier forma.
