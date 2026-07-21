# PROJECT_CONTEXT.md — EntreLíneas

> Documento de entrada (Nivel 1). Cualquier persona o agente de IA (Claude, Kiro, etc.) debería poder entender el proyecto completo leyendo solo este archivo. Para implementar un módulo específico, cargar además `specs/<módulo>.md`, las entidades relacionadas en `domain/entities.md` y las reglas de `domain/business-rules.md` (Nivel 2).

## 1. Executive Summary

EntreLíneas es una plataforma web para administrar bibliotecas personales (físicas y digitales) y fomentar la lectura compartida entre familias y pequeños clubes de lectura dentro de un grupo familiar.

No compite con Goodreads ni con Kindle. El objetivo es conectar personas mediante historias, no acumular una red social pública de lectores.

La plataforma permite: registrar libros físicos, administrar EPUB/PDF propios (sin compartirlos entre cuentas), crear grupos familiares, organizar clubes de lectura dentro del grupo, registrar préstamos físicos y turnos de lectura digital, leer con un lector integrado, comentar y reseñar, seleccionar lecturas conjuntas mediante sorteo, y ejercer control total sobre los propios datos (Ley 21.719, Chile).

## 2. Product Vision

Las historias unen a las personas. EntreLíneas busca ser el hogar digital donde las personas administran su biblioteca y comparten la experiencia de leer juntos. El foco principal son familias y pequeños clubes de lectura — no el público general de lectores.

Ver detalle en `vision.md`.

## 3. Product Principles

1. Las personas primero que los libros.
2. El usuario es dueño de su biblioteca y sus datos.
3. Privacy by Design (Ley 21.719 desde el primer sprint).
4. La app acompaña la lectura, no la reemplaza.
5. Todo debe sentirse cercano y sencillo, aunque la función sea compleja.
6. Cloud-agnostic y costo cero por defecto.
7. Mobile-first.

Ver detalle en `product-principles.md`.

## 4. El problema

Una familia con cientos de libros físicos y digitales no tenía forma sencilla de: saber qué libros tenía, compartir la biblioteca, organizar un club de lectura, elegir el siguiente libro, registrar opiniones, ni gestionar préstamos. Las soluciones actuales (Goodreads, StoryGraph, Calibre, Komga, Kavita, Audiobookshelf) cubren partes del problema — ninguna las reúne todas de forma simple y privada. Detalle completo en `research/competitors.md`.

## 5. Usuarios objetivo

Familias lectoras (caso principal), pequeños clubes de lectura dentro de un grupo familiar, lectores individuales dentro de un grupo familiar. Detalle en `research/users.md`.

## 6. Dominio (resumen)

Usuario · GrupoFamiliar · Libro · Ejemplar (físico/digital) · Club · TurnoLectura · Préstamo · Reseña · ConsentimientoDatos · ProgresoLectura · Marcador · Nota

Jerarquía social MVP: **Usuario → Grupo → Biblioteca compartida** (metadatos). No existen "grupos conectados" en el MVP.

Detalle completo en `domain/entities.md`, `domain/business-rules.md`, `domain/use-cases.md`.

## 7. Arquitectura (resumen)

```
Interface (API REST / Next.js)
      ↓
Application (casos de uso)
      ↓
Domain (entidades, reglas de negocio — sin dependencias externas)
      ↓
Infrastructure (Postgres, storage cifrado, auth JWT)
```

Clean Architecture: el dominio nunca depende de frameworks ni de la base de datos. Toda dependencia externa se accede a través de abstracciones (interfaces) definidas en la capa de aplicación. Ver `adr/0017-cloud-agnostic-abstractions.md`.

Detalle en `architecture/architecture.md`.

## 8. Stack

- **Frontend:** Next.js, React, TypeScript, Tailwind.
- **Backend:** FastAPI (Python), SQLAlchemy, Alembic.
- **Base de datos:** PostgreSQL.
- **Autenticación:** JWT custom (Access Token + Refresh Token). Ver `adr/0004-custom-jwt-authentication.md`.
- **Storage de archivos digitales:** object storage cifrado por usuario (nunca compartido entre cuentas).
- **CI/CD:** GitHub Actions.
- **Contenedores:** Docker / Docker Compose.
- **Lector integrado:** EPUB (epub.js) + PDF (PDF.js). Ver `adr/0014-integrated-reader-mvp.md`.

> **Nota:** Redis no forma parte del MVP (ver `adr/0012-no-redis-mvp.md`). Podrá introducirse en versiones futuras.

Detalle y justificación en `architecture/tech-stack.md` y `adr/0002-tech-stack.md`.

## 9. Infraestructura — prioridad de costo

```
Local (Docker) → Supabase (Postgres + Storage, free tier) → Render / Vercel (deploy) → GCP/AWS (solo si el proyecto escala y lo justifica)
```

> Supabase Auth se rechazó — se usa JWT custom. Supabase queda solo como opción de Postgres + Storage gestionado.

## 10. Restricciones permanentes

- Nunca almacenar ni distribuir un archivo digital con copyright entre distintas cuentas de usuario.
- No usar servicios pagos por defecto; preferir open source y free tiers.
- Toda integración externa debe tener interfaz (reemplazable, no acoplada a un proveedor).
- Toda dependencia de infraestructura detrás de abstracciones — cloud agnostic siempre.
- Cumplir Ley 21.719 (Chile) desde el diseño: minimización de datos, consentimiento explícito, derechos ARCO self-service, notificación de brechas en 72h, retención configurable.
- Un préstamo solo puede registrarse sobre un ejemplar físico. Los libros digitales se coordinan mediante "turno de lectura", nunca transfiriendo el archivo.
- El lector integrado solo abre archivos del usuario autenticado actual.
- No hardcodear periodos de retención — deben ser configurables.

## 11. Decisiones de alcance MVP

- Cuentas de menores: **diferidas a v2**. Todos los usuarios MVP comparten el mismo modelo de permisos.
- Grupos conectados: **eliminados del MVP**. Solo existe la jerarquía Usuario → Grupo → Biblioteca compartida.
- Clubes: solo dentro de un grupo familiar (no entre grupos distintos en el MVP).
- Redis: eliminado del MVP. JWT no requiere estado server-side.
- Search e Import: parte del módulo Library, no módulos independientes.
- Reading Selection (sorteo): spec dedicada por su complejidad.

## 12. Convenciones

REST + JSON · OpenAPI autogenerado (FastAPI) · Conventional Commits · PEP8 + Ruff (backend) · ESLint + Prettier (frontend) · Pytest · Docker obligatorio para desarrollo local.

## 13. Roadmap (resumen)

MVP → v1 → v2 → Futuro. Detalle completo en `roadmap.md` y `research/features.md`.

## 14. Reglas para agentes de IA (Steering)

Ver `steering-rules.md` — reglas permanentes que no cambian entre tareas (Clean Architecture, testing obligatorio, dependency injection, etc.). Se cargan siempre junto con este documento.

## 15. Mapa de documentos

```
docs/
├── PROJECT_CONTEXT.md      ← estás aquí
├── vision.md
├── product-principles.md
├── roadmap.md
├── glossary.md
├── steering-rules.md
├── research/{competitors,users,features}.md
├── architecture/{architecture,tech-stack,coding-standards,api,database}.md
├── ux/{sitemap,user-flows,wireframes}.md
├── domain/{entities,business-rules,use-cases}.md
├── specs/{authentication,library,clubs,loans,privacy,reading-selection}.md
└── adr/0001-0017*.md
```
