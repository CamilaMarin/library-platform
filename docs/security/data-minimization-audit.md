# Data Minimization Audit — EntreLíneas

| Metadata         | Valor                                              |
|------------------|----------------------------------------------------|
| Referencia       | Ley 21.719 — Principio de minimización de datos    |
| Requisito        | `privacy/requirements.md` Req 1.4                  |
| Fecha auditoría  | 2026-07-27                                         |
| Responsable      | Equipo de Ingeniería — Revisión DPO                |

---

## Propósito

Este documento audita cada campo almacenado en el sistema EntreLíneas y evalúa si es estrictamente necesario para la funcionalidad ofrecida, conforme al principio de minimización de datos establecido en la Ley 21.719 sobre Protección de Datos Personales de Chile.

Criterio: **un campo es necesario si eliminarlo impediría entregar la funcionalidad comprometida al usuario o cumplir una obligación legal.**

---

## 1. Módulo Identity (Identidad)

### 1.1 Entidad: User

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria UUID; necesario para referenciar al usuario en todo el sistema. |
| `name`           | PII           | Sí                        | Necesario para identificar al usuario dentro de su grupo familiar y en clubes. |
| `email`          | PII           | Sí                        | Canal único de autenticación y de notificaciones obligatorias (retención, brechas). |
| `password_hash`  | Técnico       | Sí                        | Autenticación segura; solo se almacena el hash, nunca la contraseña en claro. |
| `privacy_settings` | Personal    | Sí                        | Implementa Req 1.8 (visibilidad explícita); sin este campo no se puede respetar la voluntad del usuario. |
| `created_at`     | Operacional   | Sí                        | Necesario para calcular retención configurable (Req 1.7) y auditoría.         |

### 1.2 Entidad: DataConsent

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria para trazabilidad del consentimiento.                          |
| `user_id`        | Técnico       | Sí                        | Vincula el consentimiento al titular; obligatorio para ARCO.                  |
| `timestamp`      | Operacional   | Sí                        | Prueba temporal del consentimiento, requerido legalmente por Ley 21.719.      |
| `policy_version` | Operacional   | Sí                        | Identifica a qué versión de la política el usuario consintió.                 |
| `purpose`        | Operacional   | Sí                        | Base legal: el consentimiento debe ser específico por finalidad.              |

### 1.3 Entidad: RefreshToken

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria para gestión de sesiones.                                      |
| `user_id`        | Técnico       | Sí                        | Asocia el token al usuario; necesario para revocación selectiva.              |
| `token_hash`     | Técnico       | Sí                        | Validación segura del refresh token sin almacenar el valor en claro.          |
| `expires_at`     | Operacional   | Sí                        | Implementa expiración automática; limita ventana de exposición.               |
| `revoked_at`     | Operacional   | Sí                        | Permite revocación inmediata ante brecha (playbook de notificación).          |

### 1.4 Entidad: GroupMembership

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria.                                                               |
| `group_id`       | Operacional   | Sí                        | Identifica el grupo familiar; necesario para compartir biblioteca.            |
| `user_id`        | Técnico       | Sí                        | Asocia miembro al grupo.                                                      |
| `status`         | Operacional   | Sí                        | Controla permisos activos/inactivos; necesario para seguridad de acceso.      |
| `created_at`     | Operacional   | Sí                        | Auditoría y cálculo de retención.                                             |

---

## 2. Módulo Library (Biblioteca)

### 2.1 Entidad: Book

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria.                                                               |
| `title`          | Operacional   | Sí                        | Identificación del libro; funcionalidad core de la plataforma.                |
| `author`         | Operacional   | Sí                        | Metadato esencial para búsqueda y organización de biblioteca.                 |
| `genres`         | Operacional   | Sí                        | Necesario para selección de lectura y recomendaciones dentro del grupo.       |
| `description`    | Operacional   | Sí                        | Permite al usuario decidir si leer un libro; funcionalidad de catálogo.       |
| `pages`          | Operacional   | Sí                        | Usado en cálculo de turnos de lectura y estimaciones de préstamo.             |
| `isbn`           | Operacional   | Sí                        | Identificador estándar; necesario para deduplicación y metadatos externos.    |
| `created_at`     | Operacional   | Sí                        | Ordenamiento cronológico y retención.                                         |

### 2.2 Entidad: Copy

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria.                                                               |
| `user_id`        | Técnico       | Sí                        | Identifica al propietario del ejemplar; necesario para préstamos y permisos.  |
| `book_id`        | Técnico       | Sí                        | Vincula ejemplar con libro; relación estructural necesaria.                   |
| `type`           | Operacional   | Sí                        | Distingue formato (físico/digital); afecta lógica de préstamo y descarga.    |
| `file_ref`       | Técnico       | Sí                        | Referencia al archivo digital; sin este campo no se puede servir el contenido. |
| `status`         | Operacional   | Sí                        | Control de disponibilidad para préstamos.                                     |
| `created_at`     | Operacional   | Sí                        | Auditoría y retención.                                                        |

---

## 3. Módulo Reading Selection (Selección de Lectura)

> Los campos de este módulo son operacionales y no contienen PII. Almacenan relaciones libro-grupo para la mecánica de votación/selección.

---

## 4. Módulo Community / Clubs (Comunidad)

### 4.1 Entidad: Club

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria.                                                               |
| `name`           | Operacional   | Sí                        | Identificación del club para sus miembros.                                    |
| `group_id`       | Técnico       | Sí                        | Vincula club al grupo familiar; necesario para control de acceso.             |
| `created_by`     | Técnico       | Sí                        | Auditoría de creación; necesario para permisos de administración.             |
| `created_at`     | Operacional   | Sí                        | Auditoría y retención.                                                        |

### 4.2 Entidad: ReadingTurn

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria.                                                               |
| `club_id`        | Técnico       | Sí                        | Vincula turno al club.                                                        |
| `book_id`        | Técnico       | Sí                        | Libro asignado al turno; funcionalidad core.                                  |
| `status`         | Operacional   | Sí                        | Control del ciclo de vida del turno (activo/completado).                      |
| `started_at`     | Operacional   | Sí                        | Necesario para cronología y métricas de lectura.                              |

### 4.3 Entidad: Comment

| Campo             | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|-------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`             | Técnico       | Sí                        | Clave primaria.                                                               |
| `turn_id`        | Técnico       | Sí                        | Vincula comentario al turno de lectura.                                       |
| `user_id`        | Técnico       | Sí                        | Autoría del comentario; necesario para moderación y ARCO.                     |
| `text`           | Personal      | Sí                        | Contenido generado por el usuario; es la funcionalidad misma del módulo.      |
| `created_at`     | Operacional   | Sí                        | Ordenamiento cronológico y retención.                                         |

---

## 5. Módulo Reviews (Reseñas)

### 5.1 Entidad: Review

| Campo              | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|--------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`              | Técnico       | Sí                        | Clave primaria.                                                               |
| `user_id`         | Técnico       | Sí                        | Autoría; necesario para ARCO y control de visibilidad.                        |
| `book_id`         | Técnico       | Sí                        | Vincula reseña al libro; relación estructural.                                |
| `rating`          | Personal      | Sí                        | Opinión del usuario; funcionalidad core del módulo de reseñas.                |
| `text`            | Personal      | Sí                        | Contenido de la reseña; funcionalidad core.                                   |
| `visibility`      | Operacional   | Sí                        | Implementa Req 1.8 — visibilidad explícita configurada por el propietario.   |
| `shared_with_type`| Operacional   | Sí                        | Define el alcance del compartir (grupo, club, público); complementa visibility. |
| `shared_with_id`  | Técnico       | Sí                        | Identifica la entidad específica con quien se comparte; necesario para enforcement. |
| `created_at`      | Operacional   | Sí                        | Auditoría, ordenamiento y retención.                                          |
| `updated_at`      | Operacional   | Sí                        | Trazabilidad de modificaciones; necesario para auditoría (Req 1.5).          |

---

## 6. Módulo Circulation / Loans (Circulación / Préstamos)

### 6.1 Entidad: Loan

| Campo                  | Clasificación | ¿Estrictamente necesario? | Justificación                                                                 |
|------------------------|---------------|---------------------------|-------------------------------------------------------------------------------|
| `id`                  | Técnico       | Sí                        | Clave primaria.                                                               |
| `copy_id`             | Técnico       | Sí                        | Identifica el ejemplar prestado; relación estructural.                        |
| `borrower_user_id`    | Técnico       | Sí                        | Identifica quién recibe el préstamo; necesario para devolución y permisos.    |
| `loan_date`           | Operacional   | Sí                        | Fecha de inicio; necesaria para calcular vencimiento.                         |
| `estimated_return_date`| Operacional  | Sí                        | Fecha límite del préstamo; funcionalidad core de circulación.                 |
| `returned_date`       | Operacional   | Sí                        | Registra devolución efectiva; necesaria para liberar disponibilidad.          |
| `status`              | Operacional   | Sí                        | Estado del préstamo (activo/devuelto/vencido); control operacional.           |

---

## Conclusión

**Todos los campos pasan la prueba de minimización.** No se recopila ni almacena ningún dato personal innecesario para la funcionalidad ofrecida o para cumplir obligaciones legales.

Observaciones clave:
- No se almacenan datos biométricos, de geolocalización, ni perfiles de comportamiento.
- Las contraseñas solo se almacenan como hash (nunca en claro).
- Los tokens solo se almacenan como hash.
- Los archivos digitales se referencian por `file_ref`, no se almacena contenido inline innecesariamente.
- La clasificación `shared_with_type` + `shared_with_id` existe exclusivamente para cumplir el requisito de visibilidad explícita (Req 1.8).

---

*Próxima revisión programada: cuando se agregue un nuevo campo a cualquier entidad del sistema.*
