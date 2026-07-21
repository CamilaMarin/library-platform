# Architecture — EntreLíneas

## Estilo: Clean Architecture + Domain-Driven Design (ligero)

```
┌─────────────────────────────────────────────┐
│  Interface layer                             │
│  API REST (FastAPI) · Web (Next.js)          │
└───────────────────┬───────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Application layer                           │
│  Casos de uso (ver domain/use-cases.md)      │
│  Interfaces/protocolos para infraestructura  │
└───────────────────┬───────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Domain layer                                │
│  Entidades, value objects, reglas de negocio │
│  Sin dependencias externas (sin DB, sin HTTP)│
└───────────────────┬───────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Infrastructure layer                        │
│  PostgreSQL · Storage cifrado · JWT Auth     │
│  Implementaciones concretas de interfaces    │
└─────────────────────────────────────────────┘
```

Regla dura: el dominio nunca importa nada de infraestructura ni de framework. La infraestructura implementa interfaces definidas por el dominio/aplicación (Dependency Inversion). Ver `adr/0017-cloud-agnostic-abstractions.md`.

## Bounded contexts

1. **Identidad & Privacidad** — Usuario, ConsentimientoDatos, RefreshToken, derechos ARCO.
2. **Biblioteca** — Libro, Ejemplar, ProgresoLectura, Marcador, Nota, almacenamiento aislado por usuario, lector integrado.
3. **Comunidad** — GrupoFamiliar, Club, TurnoLectura. Clubes solo dentro de un grupo familiar en el MVP.
4. **Circulación** — Préstamo (solo físico).
5. **Reseñas** — Reseña, con visibilidad `private | shared` y destino explícito.
6. **Selección de Lectura** — Sorteo, disponibilidad por participante. Spec dedicada.

Cada contexto puede evolucionar de forma relativamente independiente; comparten identificadores (usuario_id, libro_id) pero no lógica interna.

## Abstracciones de infraestructura (cloud agnostic — ver adr/0017)

Toda dependencia externa se accede a través de interfaces definidas en el application layer:

- `FileStorage` → implementaciones: local filesystem, MinIO, S3, GCS, Supabase Storage.
- `TokenService` → implementación: JWT (PyJWT).
- `MetadataProvider` → implementaciones: Open Library, Google Books.
- `NotificationService` → implementaciones intercambiables (email, push, etc.).
- Repositorios (via SQLAlchemy) → abstraídos por protocolo/interfaz.

## Diagrama de alto nivel (infraestructura física)

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Next.js    │────▶│  FastAPI (REST)   │────▶│  PostgreSQL         │
│  (web)      │◀────│  + JWT Auth       │◀────│                     │
└─────────────┘     └──────────────────┘     └───────────────────┘
       │                      │
       │             ┌────────┴────────┐
       │             ▼                 ▼
       │    ┌─────────────────┐  ┌──────────────────┐
       │    │ Storage cifrado  │  │ Servicio de       │
       │    │ aislado por      │  │ auditoría/logs    │
       │    │ usuario          │  │ (Ley 21.719)      │
       │    └─────────────────┘  └──────────────────┘
       │
       ▼
┌─────────────────┐
│ Lector EPUB/PDF │
│ (epub.js/PDF.js)│
└─────────────────┘
```

## Por qué Clean Architecture aquí (y no algo más simple)

El proyecto es también pieza de portafolio: demostrar separación de capas, testabilidad del dominio sin mockear infraestructura, y una base que sobrevive un cambio de framework o de proveedor cloud sin reescribir reglas de negocio. Ver `adr/0002-tech-stack.md` y `adr/0017-cloud-agnostic-abstractions.md`.
