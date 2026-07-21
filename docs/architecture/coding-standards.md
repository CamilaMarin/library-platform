# Coding Standards — EntreLíneas

## Estructura de carpetas (backend, por bounded context)

```
app/
  identity/
    domain/
    application/
    infrastructure/
    interface/
  library/
    domain/
    application/
    infrastructure/
    interface/
  community/
    domain/
    application/
    infrastructure/
    interface/
  circulation/
    domain/
    application/
    infrastructure/
    interface/
  reviews/
    domain/
    application/
    infrastructure/
    interface/
  reading_selection/
    domain/
    application/
    infrastructure/
    interface/
```

> Nota: `search` e `import` viven dentro de `library/` como casos de uso, no como módulos separados (ver `adr/0010`, `adr/0011`).

## Reglas

- El **domain layer** no importa nada de FastAPI, SQLAlchemy ni ningún framework.
- Los controladores (interface layer) nunca acceden directamente a la base de datos — siempre pasan por un caso de uso (application layer).
- Toda dependencia externa se inyecta (Dependency Injection), nunca se instancia directamente dentro del dominio o los casos de uso.
- Toda dependencia de infraestructura se accede a través de interfaces/protocolos definidos en el application layer (cloud agnostic — ver `adr/0017`).
- Toda funcionalidad nueva requiere al menos un test del dominio y uno de integración del endpoint.
- Preferir claridad sobre optimización prematura.
- No agregar librerías nuevas sin justificar por qué el stdlib o lo ya instalado no alcanza.

## Estilo y linting

- Backend: PEP8 + Ruff.
- Frontend: ESLint + Prettier.

## Commits

- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Un commit = un cambio coherente y revisable.

## API

- REST + JSON.
- OpenAPI autogenerado por FastAPI, mantenido siempre actualizado (no se documenta a mano por separado).
- Autenticación: JWT custom (Access Token en header `Authorization: Bearer <token>`).

## Definition of Done (por feature)

- [ ] Cumple los acceptance criteria del spec correspondiente en `specs/`.
- [ ] Tests de dominio + integración en verde.
- [ ] Sin acceso directo a infraestructura fuera de su capa.
- [ ] Si toca datos personales: registrado en `RegistroTratamientoDatos` y cubierto por el log de auditoría.
- [ ] Documentación (`specs/`, `domain/`) actualizada si la implementación reveló un caso no contemplado.
- [ ] No introduce dependencia de proveedor cloud específico — toda integración detrás de abstracción.
