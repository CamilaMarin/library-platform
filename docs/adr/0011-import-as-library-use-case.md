# ADR-0011: Import is a Library Use Case

## Estado
Aceptado

## Contexto
El roadmap lista "Import manual + autocompletado de metadatos" como feature MVP. Se evaluó si debía ser un bounded context independiente.

## Decisión
- Import es un **caso de uso dentro del módulo Library**, no un bounded context independiente.
- El caso de uso `ImportarLibro` (o `AutocompletarMetadatos`) vive en `library/application/`.

## Consecuencias
- No se crea un directorio `import/` separado.
- La integración con fuentes externas (Open Library, Google Books) se implementa como adaptador en `library/infrastructure/`, detrás de una interfaz definida en el application layer.
- Mantiene la cohesión del bounded context Biblioteca.
