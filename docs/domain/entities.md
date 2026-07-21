# Domain Entities — EntreLíneas (DDD)

## Bounded Contexts

### 1. Identidad & Privacidad
- **Usuario** (aggregate root): id, nombre, email, password_hash, configuración_privacidad.
- **ConsentimientoDatos** (value object/entidad interna): timestamp, versión de política, finalidad.
- **RefreshToken** (entidad): token, usuario_id, expiración, revocado.

> Nota: `fecha_nacimiento` es opcional en el MVP. Cuentas de menores diferidas a v2 (ver `adr/0005-minor-accounts-deferred.md`).

### 2. Biblioteca
- **Libro** (entidad de catálogo): título, autor, géneros, descripción, páginas, ISBN. Representa la obra intelectual. Puede existir sin que nadie posea una copia.
- **Ejemplar** (aggregate root, pertenece a un Usuario): tipo (físico/digital), archivo_ref (solo digital, nunca expuesto fuera del dueño), estado. Cada copia tiene exactamente un propietario.
- **ProgresoLectura** (entidad dentro del aggregate Ejemplar digital): usuario_id, ejemplar_id, posición, porcentaje, última_lectura.
- **Marcador** (entidad): usuario_id, ejemplar_id, posición, etiqueta.
- **Nota** (entidad): usuario_id, ejemplar_id, posición, texto.

### 3. Comunidad
- **GrupoFamiliar** (aggregate root): lista de miembros con estado (invitado/aceptado).
- **Club** (aggregate root): grupo asociado (solo un grupo en MVP), libro activo, fecha de discusión.
- **TurnoLectura** (entidad dentro del aggregate Club): usuario con el turno actual, comentarios.

> Nota: En el MVP los clubes solo existen dentro de un grupo familiar. "Grupos conectados" eliminados del MVP (ver `adr/0006-no-connected-groups-mvp.md`).

### 4. Circulación
- **Préstamo** (aggregate root): referencia a un Ejemplar de tipo físico exclusivamente, prestatario, fechas, estado.

### 5. Reseñas
- **Reseña** (aggregate root): usuario, libro, calificación, texto, visibility (`private` | `shared`), shared_with_type, shared_with_id.

> Nota: Visibilidad usa modelo `visibility` + `shared_with` explícito, no el antiguo `private|group|club` (ver `adr/0007-review-visibility-model.md`).

### 6. Selección de Lectura
- **Sorteo** (entidad): grupo_id, filtros aplicados, resultado, timestamp.
- La lógica de disponibilidad valida que cada participante tenga acceso autorizado al libro (ver `adr/0008-reading-selection-availability.md`).

## Invariantes de agregado (resumen — detalle en business-rules.md)

- Un `Ejemplar` de tipo digital solo puede tener un `usuario_id` propietario, inmutable tras la creación.
- Un `Préstamo` solo puede crearse referenciando un `Ejemplar` con `tipo = fisico`.
- Un `TurnoLectura` no puede activarse para un usuario que no posea su propio `Ejemplar` del `Libro` en cuestión.
- El lector integrado solo puede abrir un archivo cuyo `ejemplar.usuario_id == request.user_id`.

## Relación entre contextos

Los contextos comparten identificadores (`usuario_id`, `libro_id`) pero no comparten modelos internos — por ejemplo, "Comunidad" no conoce el `archivo_ref` de un Ejemplar, solo sabe que existe y a quién pertenece.
