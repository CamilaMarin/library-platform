# Use Cases — EntreLíneas (Application Layer)

## Identidad & Privacidad
- `RegistrarUsuario` (requiere `AceptarConsentimientoDatos` previo o en el mismo flujo)
- `LoginUsuario` (emite Access Token + Refresh Token; ver `adr/0004`)
- `RefrescarToken` (rota Refresh Token, emite nuevo Access Token)
- `RevocarToken` (invalida Refresh Token)
- `CrearGrupoFamiliar`
- `InvitarMiembroGrupo` / `AceptarInvitacionGrupo`
- `EjercerDerechoARCO` (acceso / rectificación / cancelación / oposición / portabilidad)
- `NotificarBrechaDeSeguridad` (uso interno, dispara playbook de 72h)

## Biblioteca
- `AgregarLibro` (metadatos de la obra intelectual)
- `AgregarEjemplarFisico`
- `AgregarEjemplarDigital` (incluye cifrado y aislamiento de archivo)
- `EditarLibro` / `EliminarLibro`
- `EditarEjemplar` / `EliminarEjemplar`
- `BuscarLibro` (búsqueda dentro de biblioteca propia y del grupo — solo metadatos)
- `ImportarMetadatosLibro` (autocompletado vía fuente pública: Open Library, Google Books)
- `AbrirLector` (valida propiedad, sirve archivo cifrado al propietario autenticado)
- `GuardarProgresoLectura`
- `CrearMarcador` / `EliminarMarcador`
- `CrearNota` / `EditarNota` / `EliminarNota`

## Selección de Lectura
- `EjecutarSorteoLectura` (valida disponibilidad para todos los participantes; ver `adr/0008`)
- `SeleccionPorTurno` (modo alternativo de elección rotativa entre miembros)

## Comunidad
- `CrearClub` (solo dentro de un grupo familiar en el MVP; ver `adr/0006`)
- `AsignarLibroActivoClub`
- `ActivarTurnoLectura` (valida posesión de ejemplar propio)
- `ComentarEnClub`

## Circulación
- `RegistrarPrestamo` (solo ejemplar físico)
- `RegistrarDevolucionPrestamo`

## Reseñas
- `CrearResena` (con `visibility`: private | shared, y `shared_with` explícito; ver `adr/0007`)
- `EditarResena` / `EliminarResena`
