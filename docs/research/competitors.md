# Research — Competitors

## Panorama

Dos categorías de referentes, que resuelven partes distintas del problema:

**A. Sociales / tracking público:** Goodreads, StoryGraph, Hardcover, Fable.
**B. Self-hosted / biblioteca personal:** Calibre, Komga, Kavita, Audiobookshelf, Jellyfin (+ plugin Bookshelf), OpenLibrary (fuente de metadatos, no gestor).

Ninguno cruza ambas categorías con un círculo social cerrado (familiar).

## Comparativo

| Herramienta | Biblioteca propia (EPUB/PDF) | Social | Clubes de lectura | Círculo cerrado/familiar | Préstamos | Multiusuario nativo |
|---|---|---|---|---|---|---|
| Goodreads | ❌ | ✅ público | Grupos ⚠️ básico | ❌ | ❌ | — |
| StoryGraph | ❌ | ✅ público | Grupos ⚠️ básico | Parcial (amigos) | ❌ | — |
| Fable | ❌ | ✅ público | ✅ (clubes con expertos/celebridades) | ❌ | ❌ | — |
| Hardcover | ❌ | ✅ público | ⚠️ básico | ❌ | ❌ | — |
| Calibre | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ (single-user, desktop) |
| Komga | ✅ (fuerte en cómics/manga) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Kavita | ✅ (formato más amplio: EPUB/PDF/CBZ/CBR/CB7) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Audiobookshelf | ⚠️ (enfocado en audiolibros/podcasts; lector EPUB básico incluido) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Jellyfin (+ Bookshelf) | ⚠️ (requiere plugin, más básico) | ❌ | ❌ | ❌ | ❌ | ✅ |
| **EntreLíneas** | ✅ | ❌ (por diseño) | ✅ | ✅ | ✅ (físico) | ✅ (por grupo familiar) |

## Notas por herramienta

- **Kavita** es hoy la opción self-hosted más completa para ebooks/manga/cómics: soporta el rango más amplio de formatos, no depende de Calibre, e incluye OPDS para lectores externos. Es la referencia técnica más cercana a "administrar mi propia biblioteca digital" — pero sigue siendo estrictamente individual, sin ninguna capa social.
- **Audiobookshelf** está especializado en audiolibros y podcasts (capítulos, marcadores, velocidad de reproducción, apps móviles dedicadas); su soporte de EPUB es secundario y básico.
- **Jellyfin** necesita un plugin de terceros para libros y queda por detrás de Kavita/Audiobookshelf en esa función específica — su fortaleza real es video.
- **Calibre** sigue siendo la referencia de gestión/conversión de metadatos, pero es una app de escritorio individual sin capa multiusuario ni social.
- **Fable** es el competidor más cercano en "clubes de lectura con mecánica real", pero está diseñado para clubes públicos o temáticos, no para el círculo familiar cerrado.

## El hueco de mercado

Nadie cruza gestión de biblioteca propia (terreno de Calibre/Komga/Kavita) con experiencia social de círculo cerrado y mecánicas de decisión conjunta (sorteo, rotación, préstamos internos). Ese cruce es EntreLíneas.

**Posicionamiento:**
> "Kavita organiza tu biblioteca. Goodreads conecta lectores. EntreLíneas hace que tu familia lea la misma historia."

## Preguntas abiertas para refinar backlog

- ¿Qué odian los usuarios de Goodreads? → UI anticuada, sin media estrellas pese a años de pedirlo, feed poco curado.
- ¿Qué piden hace años y nunca implementaron? → Goodreads: calificación con decimales; StoryGraph: mejor soporte de EPUB/import.
- ¿Qué no deberíamos copiar? → El feed público infinito tipo red social; la promesa de "biblioteca ilimitada" sin dueño claro del archivo (riesgo legal, ver `adr/0001-no-shared-file-storage.md`).
