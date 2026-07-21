# ADR-0009: Digital Books — Strict Isolation

## Estado
Aceptado

## Contexto
Complementa y refuerza ADR-0001 con decisiones operativas específicas para el MVP.

## Decisión
- EntreLíneas **nunca redistribuye** libros digitales con copyright.
- Los archivos EPUB/PDF subidos permanecen **estrictamente privados** del usuario que los subió.
- Las bibliotecas compartidas (visibles al grupo) exponen **solo metadatos**, nunca archivos.
- El lector integrado solo abre archivos que pertenecen al usuario autenticado actual.
- **No existirá ninguna funcionalidad de compartir archivos en el MVP.**

## Consecuencias
- El endpoint de descarga/lectura valida `request.user_id == ejemplar.usuario_id` como invariante absoluto.
- La biblioteca compartida del grupo es un catálogo de metadatos — nunca un repositorio de archivos accesibles por otros.
- Se alinea con la posición legal de *Hachette v. Internet Archive* y con el principio de propiedad del usuario.
