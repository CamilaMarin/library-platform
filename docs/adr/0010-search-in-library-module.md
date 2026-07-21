# ADR-0010: Search is Part of the Library Module

## Estado
Aceptado

## Contexto
El roadmap lista "Búsqueda básica" como feature MVP. Se evaluó si debía ser un módulo independiente o parte de un bounded context existente.

## Decisión
- La búsqueda es parte del módulo **Library** (bounded context Biblioteca).
- No es un módulo independiente ni un bounded context separado.

## Consecuencias
- Los casos de uso de búsqueda (`BuscarLibro`, `BuscarEjemplar`) viven en `library/application/`.
- No se crea un directorio `search/` separado en la estructura de carpetas.
- Si en el futuro la búsqueda crece en complejidad (full-text, Elasticsearch), se puede extraer a infraestructura propia manteniendo la interfaz en el módulo Library.
