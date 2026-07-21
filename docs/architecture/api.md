# API — EntreLíneas (resumen de recursos)

REST + JSON. OpenAPI autogenerado por FastAPI (fuente de verdad para el contrato exacto; este archivo es un mapa de alto nivel).

## Autenticación (JWT custom — ver adr/0004)

- `POST /auth/register` — registro de usuario (requiere consentimiento en el mismo flujo)
- `POST /auth/consent` — aceptación explícita de consentimiento de datos
- `POST /auth/login` — login, devuelve Access Token + Refresh Token
- `POST /auth/refresh` — rota Refresh Token, emite nuevo Access Token
- `POST /auth/logout` — revoca Refresh Token

## Usuarios

- `GET /users/me` — perfil propio
- `PATCH /users/me` — actualizar perfil
- `DELETE /users/me` — cancelación de cuenta (dispara flujo ARCO de cancelación)
- `GET /users/me/export` — portabilidad de datos (ARCO)

## Grupos familiares

- `POST /groups` — crear grupo familiar
- `GET /groups/{id}` — detalle del grupo
- `POST /groups/{id}/invitations` — invitar miembro
- `POST /groups/{id}/invitations/{id}/accept` — aceptar invitación

## Biblioteca (Books + Copies)

- `POST /books` — crear libro (metadatos de la obra)
- `GET /books?query=` — búsqueda de libros (metadatos, autocompletado externo)
- `PATCH /books/{id}` — editar metadatos
- `DELETE /books/{id}` — eliminar libro
- `POST /copies` — crear ejemplar (físico o digital; digital requiere upload cifrado separado)
- `GET /copies/{id}` — detalle de ejemplar
- `PATCH /copies/{id}` — editar ejemplar
- `DELETE /copies/{id}` — eliminar ejemplar

## Lector integrado (ver adr/0014)

- `GET /copies/{id}/file` — servir archivo cifrado (solo al propietario autenticado)
- `GET /copies/{id}/progress` — obtener progreso de lectura
- `PUT /copies/{id}/progress` — guardar progreso de lectura
- `POST /copies/{id}/bookmarks` — crear marcador
- `DELETE /copies/{id}/bookmarks/{bookmark_id}` — eliminar marcador
- `POST /copies/{id}/notes` — crear nota
- `PATCH /copies/{id}/notes/{note_id}` — editar nota
- `DELETE /copies/{id}/notes/{note_id}` — eliminar nota

## Selección de lectura (ver adr/0013)

- `POST /groups/{id}/draws` — ejecutar sorteo (con filtros en body)
- `GET /groups/{id}/draws` — historial de sorteos del grupo

## Préstamos (solo ejemplares físicos)

- `POST /copies/{id}/loans` — registrar préstamo
- `PATCH /loans/{id}/return` — registrar devolución

## Clubes (solo dentro de un grupo familiar en MVP — ver adr/0006)

- `POST /clubs` — crear club (asociado a un grupo)
- `GET /clubs/{id}` — detalle de club
- `PATCH /clubs/{id}/active-book` — asignar libro activo
- `POST /clubs/{id}/comments` — comentar en club
- `POST /clubs/{id}/reading-turns` — crear turno de lectura
- `PATCH /reading-turns/{id}` — actualizar turno

## Reseñas (ver adr/0007 para modelo de visibilidad)

- `POST /reviews` — crear reseña (con `visibility`: private | shared, `shared_with`: {type, id})
- `PATCH /reviews/{id}` — editar reseña
- `DELETE /reviews/{id}` — eliminar reseña

## Privacidad & Auditoría

- `GET /privacy/processing-record` — registro de tratamiento (uso interno/auditoría)

## Convenciones

- Todos los endpoints devuelven errores en formato consistente (`{ "error": { "code", "message" } }`).
- Ningún endpoint de `copies` permite `GET` del archivo digital de un `usuario_id` distinto al dueño — se valida en el application layer, no solo en la UI.
- Endpoints que tocan datos personales registran automáticamente en el log de auditoría (middleware transversal).
- Access Token requerido en header `Authorization: Bearer <token>` para todos los endpoints autenticados.
