# Spec — Library (Books & Copies)

## Requirement: Gestión de biblioteca personal

**User Story:** Como lector, quiero registrar los libros que tengo (físicos y digitales) con su género y una breve descripción, para verlos todos juntos y decidir qué leer.

### Acceptance Criteria
1. CUANDO un usuario agrega un libro, EL SISTEMA DEBERÁ permitir crear la obra (metadatos) y luego asociar uno o más ejemplares (copias).
2. CUANDO un ejemplar es "digital", EL SISTEMA DEBERÁ almacenar el archivo cifrado, asociado únicamente a la cuenta que lo subió.
3. CUANDO un ejemplar es "físico", EL SISTEMA DEBERÁ almacenar solo metadatos y estado de disponibilidad, sin archivo.
4. EL SISTEMA DEBERÁ permitir asignar género(s), descripción y páginas a cada libro.
5. SI el usuario busca por título/ISBN, ENTONCES EL SISTEMA DEBERÁ autocompletar metadatos desde una fuente pública (detrás de una interfaz reemplazable), dejando la carga del archivo/ejemplar como paso separado.
6. EL SISTEMA DEBERÁ permitir editar o eliminar cualquier libro/ejemplar en cualquier momento.

> Referencia modelo: `adr/0015-book-copy-separation.md` — Book representa la obra, Copy representa una copia poseída.

## Requirement: Búsqueda

### Acceptance Criteria
1. EL SISTEMA DEBERÁ ofrecer búsqueda de libros dentro de la biblioteca propia y del grupo (solo metadatos, nunca archivos).
2. La búsqueda es parte del módulo Library, no un módulo independiente (ver `adr/0010-search-in-library-module.md`).

## Requirement: Import de metadatos

### Acceptance Criteria
1. EL SISTEMA DEBERÁ permitir autocompletar metadatos de un libro a partir de ISBN o título, consultando fuentes públicas (Open Library, Google Books).
2. Import es un caso de uso de Library, no un bounded context independiente (ver `adr/0011-import-as-library-use-case.md`).

## Requirement: Lector integrado

**User Story:** Como lector digital, quiero abrir mis EPUB/PDF directamente en la plataforma, con mi progreso guardado.

### Acceptance Criteria
1. EL SISTEMA DEBERÁ incluir un lector integrado de EPUB y PDF en el MVP.
2. EL SISTEMA DEBERÁ abrir solo archivos subidos por el usuario autenticado actual — nunca archivos de otro usuario.
3. EL SISTEMA DEBERÁ almacenar progreso de lectura, marcadores y notas, asociados al usuario y al ejemplar.
4. Los datos del lector (progreso, notas, marcadores) son datos personales cubiertos por Ley 21.719.

> Referencia: `adr/0014-integrated-reader-mvp.md`

> Nota: La selección conjunta de lectura (sorteo) tiene su propia spec dedicada: `specs/reading-selection.md` (ver `adr/0013-reading-selection-dedicated-spec.md`).
