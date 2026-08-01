# View Registered Oppositions — Bugfix Design

## Overview

El usuario no puede verificar sus oposiciones ARCO activas porque: (1) el backend no expone un
endpoint `GET /users/me/oppositions` que lea `user.privacy_settings["opposed_purposes"]`, y (2)
el frontend `OppositionForm` solo muestra el formulario de alta sin renderizar la lista existente.

El fix es mínimo y no requiere cambios al modelo de datos ni migraciones: los datos ya están
persistidos correctamente por `OpposeDataProcessing`. Solo se añade un caso de uso de lectura,
un schema de respuesta, un endpoint y actualizaciones al componente de UI.

---

## Glossary

- **Bug_Condition (C)**: La condición que activa el bug — cuando el usuario intenta ver sus
  oposiciones registradas y el sistema no puede mostrárselas (endpoint inexistente, UI ausente).
- **Property (P)**: El comportamiento deseado — `GET /users/me/oppositions` devuelve la lista
  exacta de propósitos almacenados en `privacy_settings["opposed_purposes"]`, y el frontend la
  muestra sin recargar la página tras un nuevo registro.
- **Preservation**: El comportamiento de `POST /users/me/oppose` y el resto de la UI ARCO que
  debe permanecer sin cambios tras el fix.
- **`OpposeDataProcessing`**: Caso de uso en
  `backend/app/identity/application/oppose_data_processing.py` que guarda la oposición en
  `user.privacy_settings["opposed_purposes"]`.
- **`opposed_purposes`**: Lista de strings dentro del campo `privacy_settings: dict` del
  `User` entity. Es la única fuente de verdad para las oposiciones registradas.
- **`OppositionForm`**: Componente React en `frontend/src/app/settings/page.tsx` que gestiona
  el formulario de alta de oposiciones.

---

## Bug Details

### Bug Condition

El bug se manifiesta en dos capas simultáneas:

1. **Backend**: no existe ningún handler para `GET /users/me/oppositions`. Cualquier petición
   a ese endpoint devuelve `404 Not Found`.
2. **Frontend**: `OppositionForm` no consulta las oposiciones al montar y no renderiza ninguna
   lista. El usuario ve solo el formulario de alta, sin feedback sobre sus oposiciones previas.

**Formal Specification:**

```
FUNCTION isBugCondition(context)
  INPUT: context con { endpoint_exists: bool, ui_shows_list: bool }
  OUTPUT: boolean

  RETURN NOT context.endpoint_exists
         OR NOT context.ui_shows_list
END FUNCTION
```

### Examples

- **Ejemplo 1**: Usuario navega a `/settings`. Esperado: ver lista de oposiciones activas
  (posiblemente vacía). Actual: lista no existe en la UI.
- **Ejemplo 2**: Usuario registra oposición "Recomendaciones de lectura". Esperado: la nueva
  oposición aparece inmediatamente en la lista visible. Actual: se muestra confirmación pero
  no hay lista donde aparezca.
- **Ejemplo 3**: Frontend hace `GET /api/users/me/oppositions`. Esperado: `200 OK` con
  `{"opposed_purposes": ["Recomendaciones de lectura"]}`. Actual: `404 Not Found`.
- **Edge case**: Usuario sin oposiciones registradas navega al panel. Esperado: lista vacía
  con mensaje informativo. La lista vacía es un estado válido, no un error.

---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- `POST /users/me/oppose` debe continuar registrando oposiciones exactamente como antes,
  devolviendo `OpposeResponse` con `opposed: true`.
- El formulario `OppositionForm` con chips predefinidos y campo libre debe seguir funcionando
  idéntico para el flujo de alta.
- Los demás derechos ARCO (Acceso/export, Rectificación/perfil, Cancelación/delete) no
  deben verse afectados.
- Los endpoints `GET /users/me/export`, `PATCH /users/me` y `DELETE /users/me` deben
  continuar sin modificaciones.
- Un usuario no autenticado que llame a `GET /users/me/oppositions` debe recibir `401`,
  igual que todos los endpoints `/users/me/*`.

**Scope:**
Todo lo que no involucre la lectura de `opposed_purposes` queda completamente inalterado.

---

## Hypothesized Root Cause

La causa no es un defecto en código existente sino una **funcionalidad nunca implementada**:

1. **Endpoint GET ausente**: `users_router.py` tiene `POST /users/me/oppose` pero nunca se
   creó el handler de lectura correspondiente. La ruta simplemente no existe en el router.

2. **Caso de uso de lectura ausente**: Existe `OpposeDataProcessing` (escritura) pero no
   hay un `GetUserOppositions` (lectura). El patrón del bounded context exige un caso de uso
   por operación.

3. **UI incompleta**: `OppositionForm` fue implementado solo para el flujo de alta. No
   hay llamada a ningún endpoint en `useEffect` ni estado para almacenar la lista. La
   confirmación tras el envío restablece el formulario pero no actualiza ninguna lista.

---

## Correctness Properties

Property 1: Bug Condition — La lista devuelta refleja exactamente los propósitos registrados

_For any_ usuario autenticado con N propósitos almacenados en
`privacy_settings["opposed_purposes"]`, el endpoint `GET /users/me/oppositions` SHALL
devolver `{"opposed_purposes": [...]}` con exactamente esos N propósitos, en cualquier orden.
Si N = 0, SHALL devolver `{"opposed_purposes": []}`.

**Validates: Requirements 2.3**

Property 2: Preservación — UI actualiza sin recarga tras registro exitoso

_For any_ oposición registrada con éxito via `POST /users/me/oppose`, la lista visible en
`OppositionForm` SHALL incluir el nuevo propósito sin requerir recarga de página (optimistic
update o re-fetch inmediato post-submit).

**Validates: Requirements 2.1, 2.2**

Property 3: Preservación — Comportamiento del POST inalterado

_For any_ input que no sea una llamada al nuevo `GET /users/me/oppositions` o cambios en la
UI de lista, el comportamiento de `POST /users/me/oppose` SHALL ser idéntico al comportamiento
previo al fix: misma respuesta `OpposeResponse`, mismo audit log, misma persistencia.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

---

## Fix Implementation

### Changes Required

#### 1. Nuevo caso de uso (solo lectura)

**File**: `backend/app/identity/application/get_user_oppositions.py` *(nuevo)*

**Responsabilidad**: Leer `privacy_settings["opposed_purposes"]` para un `user_id` dado.

```python
# Pseudocode
class GetUserOppositions:
    def execute(self, user_id: UUID) -> list[str]:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        self._audit_service.log(
            actor_user_id=user_id,
            action=AuditAction.ARCO_REQUEST,   # reutiliza ARCO_REQUEST (lectura ARCO)
            affected_entity=f"user:{user_id}:oppositions",
        )
        return user.privacy_settings.get("opposed_purposes", [])
```

**Nota de diseño**: Se reutiliza `AuditAction.ARCO_REQUEST` en lugar de crear un nuevo valor
de enum. La oposición ya fue auditada como `ARCO_OPPOSE` en el POST. La lectura es una
operación de acceso, coherente con `ARCO_REQUEST`.

#### 2. Nuevo schema de respuesta

**File**: `backend/app/identity/interface/schemas.py` *(modificado)*

```python
class OppositionsResponse(BaseModel):
    """Response body for GET /users/me/oppositions."""
    opposed_purposes: list[str]
```

#### 3. Nuevo endpoint GET

**File**: `backend/app/identity/interface/users_router.py` *(modificado)*

```python
@router.get("/me/oppositions", response_model=OppositionsResponse)
def get_user_oppositions(
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List all active data processing oppositions for the authenticated user.
    ARCO opposition right — read access.
    """
    user_repo = SqlUserRepository(db)
    audit_repo = SqlAuditLogRepository(db)
    audit_service = AuditService(repository=audit_repo)
    use_case = GetUserOppositions(
        user_repository=user_repo,
        audit_service=audit_service,
    )
    try:
        purposes = use_case.execute(current_user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="user_not_found")
    db.commit()
    return OppositionsResponse(opposed_purposes=purposes)
```

**Nota**: El import de `GetUserOppositions` y su `UserNotFoundError` se añaden al bloque de
imports existente, siguiendo el patrón del resto del router.

#### 4. Nuevo tipo TypeScript

**File**: `frontend/src/types/index.ts` *(modificado)*

```typescript
export interface OppositionsResponse {
  opposed_purposes: string[];
}
```

Se añade en la sección `// === Settings / Privacy ===`, junto a `OpposeRequest` y
`OpposeResponse`.

#### 5. Actualización de `OppositionForm`

**File**: `frontend/src/app/settings/page.tsx` *(modificado)*

Cambios en el componente `OppositionForm`:

- **Estado nuevo**: `const [activeOppositions, setActiveOppositions] = useState<string[]>([])`
- **Estado nuevo**: `const [loadingOppositions, setLoadingOppositions] = useState(true)`
- **useEffect al montar**: fetch `GET /users/me/oppositions`, guardar resultado en
  `activeOppositions`. Si falla, loguear silenciosamente (no bloquear UI principal).
- **Tras submit exitoso**: añadir el nuevo `purpose` a `activeOppositions` (optimistic update)
  en lugar de esperar un re-fetch.
- **Render**: mostrar la lista sobre el botón/formulario de alta. Si `loadingOppositions`,
  mostrar skeleton/loading state. Si lista vacía, mostrar texto "No tienes oposiciones
  registradas aún." Si hay items, renderizar chips de solo lectura con
  `var(--color-teak)` como color de acento.

**Diseño de la lista (chips de solo lectura):**

```tsx
// Cada chip en la lista de oposiciones activas
<span
  className="rounded-full px-3 py-1 text-sm"
  style={{
    border: "1px solid var(--color-teak)",
    color: "var(--color-teak)",
    background: "transparent",
  }}
>
  {purpose}
</span>
```

**Tipo añadido al import**: `OppositionsResponse` desde `@/types`.

---

## Testing Strategy

### Validation Approach

Dos fases: primero confirmar el bug en código sin fix (exploratory), luego verificar el fix
con tests de propiedad y de preservación.

### Exploratory Bug Condition Checking

**Goal**: Confirmar que `GET /users/me/oppositions` retorna 404 antes del fix y que la UI
no muestra lista alguna.

**Test Plan**: Tests de integración que autentican un usuario, registran oposiciones via
`POST /users/me/oppose`, y luego llaman a `GET /users/me/oppositions`. En código sin fix,
estos tests deben fallar con 404.

**Test Cases**:
1. **GET sin fix**: `GET /users/me/oppositions` con token válido → esperado `200`, actual
   `404` (falla en código sin fix).
2. **GET con usuario sin oposiciones**: esperado `{"opposed_purposes": []}`, actual `404`.
3. **GET después de POST**: registrar oposición y listarla → esperado propósito en lista,
   actual `404`.

**Expected Counterexamples**:
- El endpoint no existe: FastAPI retorna `404 Not Found` para todas las llamadas.

### Fix Checking

**Goal**: Verificar que con el fix aplicado, `GET /users/me/oppositions` devuelve
exactamente los propósitos registrados.

**Pseudocode:**
```
FOR ALL usuario WITH N propósitos en privacy_settings["opposed_purposes"] DO
  response := GET /users/me/oppositions (autenticado)
  ASSERT response.status == 200
  ASSERT set(response.opposed_purposes) == set(privacy_settings["opposed_purposes"])
  ASSERT len(response.opposed_purposes) == N
END FOR
```

**Casos específicos**:
- N = 0: `{"opposed_purposes": []}` con status 200.
- N = 1: lista con un elemento.
- N = 3 (con duplicados intentados via POST): lista sin duplicados (invariante de
  `OpposeDataProcessing`).
- Usuario no autenticado: `401`.
- `user_id` válido en token pero no existe en DB: `404`.

### Preservation Checking

**Goal**: Verificar que `POST /users/me/oppose` produce exactamente el mismo resultado
antes y después del fix.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT POST_original(input) == POST_fixed(input)
END FOR
```

**Testing Approach**: Los tests de integración existentes para `POST /users/me/oppose`
deben pasar sin modificación tras el fix. Property-based testing con Hypothesis para
generar propósitos aleatorios y verificar idempotencia del POST.

**Test Cases**:
1. **POST preservation**: registrar oposición con propósito arbitrario → response
   `OpposeResponse(opposed=True)` inalterada.
2. **POST idempotencia**: registrar el mismo propósito dos veces → lista no tiene duplicados
   (comportamiento ya implementado en `OpposeDataProcessing`).
3. **Otros endpoints ARCO**: `GET /users/me/export`, `PATCH /users/me`, `DELETE /users/me`
   responden igual que antes.
4. **Auth 401**: endpoint nuevo respeta el mismo guard `get_current_user_id`.

### Unit Tests

- `GetUserOppositions.execute()` con usuario que tiene oposiciones → retorna lista correcta.
- `GetUserOppositions.execute()` con usuario sin oposiciones → retorna `[]`.
- `GetUserOppositions.execute()` con `user_id` inexistente → lanza `UserNotFoundError`.
- `GetUserOppositions.execute()` verifica que el audit log es llamado con `ARCO_REQUEST`.
- `OppositionsResponse` schema serializa correctamente lista vacía y lista con elementos.

### Property-Based Tests

- **[Hypothesis]** Para cualquier lista de propósitos registrados via `OpposeDataProcessing`,
  `GetUserOppositions` devuelve exactamente esos propósitos (Property 1).
- **[Hypothesis]** Para cualquier propósito `p` registrado via POST, la lista devuelta por GET
  contiene `p` (Property 2 — sin recarga).
- **[Hypothesis]** El comportamiento de `OpposeDataProcessing` no cambia tras añadir
  `GetUserOppositions` al router (Property 3 — preservación).

### Integration Tests

- `GET /users/me/oppositions` con usuario autenticado y 0 oposiciones → `200 {"opposed_purposes": []}`.
- `GET /users/me/oppositions` después de `POST /users/me/oppose` con propósito X → lista
  contiene X.
- `GET /users/me/oppositions` sin token → `401`.
- `POST /users/me/oppose` sigue funcionando después de añadir el nuevo endpoint (sin regressions).
