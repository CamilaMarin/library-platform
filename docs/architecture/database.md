# Database — EntreLíneas

PostgreSQL. Ver también `domain/entities.md` para la versión DDD del mismo modelo.

## Tablas MVP

### Identidad & Privacidad
- **usuarios**(id, nombre, email, password_hash, fecha_nacimiento[opcional], config_privacidad, creado_en)
- **consentimientos_datos**(id, usuario_id, timestamp, version_politica, finalidad)
- **refresh_tokens**(id, usuario_id, token_hash, expira_en, revocado, creado_en)
- **grupos_familiares**(id, nombre, creado_en)
- **miembros_grupo**(grupo_id, usuario_id, estado[invitado|aceptado])

### Biblioteca
- **libros**(id, titulo, autor, generos[], descripcion, paginas, isbn)
- **ejemplares**(id, usuario_id, libro_id, tipo[fisico|digital], archivo_ref, estado[disponible|prestado])
- **progreso_lectura**(id, usuario_id, ejemplar_id, posicion, porcentaje, ultima_lectura)
- **marcadores**(id, usuario_id, ejemplar_id, posicion, etiqueta, creado_en)
- **notas**(id, usuario_id, ejemplar_id, posicion, texto, creado_en, actualizado_en)

### Comunidad
- **clubes**(id, grupo_id, nombre, libro_activo_id, fecha_discusion)
- **turnos_lectura**(id, club_id, libro_id, usuario_id_actual)
- **comentarios_turno**(id, turno_id, usuario_id, texto, es_spoiler)

### Circulación
- **prestamos**(id, ejemplar_id, prestado_a_usuario_id, fecha_prestamo, fecha_devolucion_estimada, estado)

### Reseñas
- **resenas**(id, usuario_id, libro_id, calificacion, texto, visibility[private|shared], shared_with_type[group|club|null], shared_with_id[nullable])

### Privacidad & Auditoría
- **registro_tratamiento_datos**(id, usuario_id, tipo_dato, finalidad, base_legal, fecha_recoleccion, fecha_expiracion_retencion)
- **logs_auditoria**(id, usuario_id_actor, accion, entidad_afectada, timestamp)
- **politicas_retencion**(id, tipo_dato, duracion_dias, descripcion, activa)

### Selección de Lectura
- **sorteos**(id, grupo_id, filtros_json, resultado_libro_id, resultado_ejemplar_origen_usuario_id, timestamp)

## Constraints relevantes a nivel de aplicación (no solo DB)

- `ejemplares.archivo_ref` solo se resuelve para requests donde `request.usuario_id == ejemplares.usuario_id`.
- `prestamos.ejemplar_id` debe referenciar un ejemplar con `tipo = 'fisico'` (validado en el caso de uso, reforzado con constraint check si el motor lo permite).
- `resenas.shared_with_id` solo puede ser NOT NULL cuando `visibility = 'shared'`.
- `progreso_lectura`, `marcadores` y `notas` solo pueden existir para ejemplares digitales cuyo `usuario_id` coincida con el del registro.

## Cambios respecto al diseño anterior

- Se eliminó `rol[adulto|menor]` de `miembros_grupo` — cuentas de menores diferidas a v2 (ver `adr/0005`).
- Se agregó `refresh_tokens` — JWT custom con rotación (ver `adr/0004`).
- Se cambió `resenas.visibilidad` por el modelo `visibility` + `shared_with_type` + `shared_with_id` (ver `adr/0007`).
- Se agregaron tablas del lector integrado: `progreso_lectura`, `marcadores`, `notas` (ver `adr/0014`).
- Se agregó `politicas_retencion` — periodos configurables, no hardcodeados (ver `adr/0016`).
- Se agregó `sorteos` — selección de lectura como feature dedicada (ver `adr/0013`).

## Tablas v2 (catálogo enriquecido, no MVP)

- **autores**, **series**, **editoriales**, **colecciones** — normalización de metadatos hoy embebidos como texto libre en `libros`.
- Campos/tablas para gestión de cuentas de menores (ver `adr/0005`).

## Índices sugeridos

- `ejemplares(usuario_id)`, `ejemplares(libro_id)` — consultas de biblioteca personal y de sorteo.
- `logs_auditoria(usuario_id_actor, timestamp)` — consultas de auditoría por rango de fecha.
- `refresh_tokens(token_hash)` — validación rápida de refresh tokens.
- `progreso_lectura(usuario_id, ejemplar_id)` — consulta de progreso al abrir lector.
