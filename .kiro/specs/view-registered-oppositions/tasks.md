# Implementation Plan: View Registered Oppositions (Bugfix)

## Overview

Bugfix para el derecho ARCO de Oposición. Los datos ya están persistidos correctamente por
`OpposeDataProcessing` en `privacy_settings["opposed_purposes"]`. El fix añade la capa de
lectura que falta: un caso de uso `GetUserOppositions`, un schema `OppositionsResponse`, el
endpoint `GET /users/me/oppositions`, el tipo TypeScript correspondiente, y la integración en
`OppositionForm` (fetch al montar + lista de chips + optimistic update).

La metodología sigue el orden explorar → preservar → implementar → validar.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - GET /users/me/oppositions returns 404 (endpoint inexistente)
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **GOAL**: Surface the counterexample concreto que demuestra que el endpoint no existe
  - **Scoped PBT Approach**: Para este bug determinístico, el caso concreto es suficiente:
    registrar N oposiciones via `POST /users/me/oppose` (flujo ya funcional) y luego llamar
    a `GET /users/me/oppositions` con el mismo token válido
  - Crear `backend/tests/test_get_user_oppositions_exploration.py`
  - Usar `TestClient` + helper `_register_and_login` (patrón de `test_arco_integration.py`)
  - Test 1: usuario con 0 oposiciones llama `GET /users/me/oppositions` → esperado `200`,
    actual `404` en código sin fix
  - Test 2: usuario que hizo `POST /users/me/oppose` con "Recomendaciones de lectura" llama
    `GET /users/me/oppositions` → esperado `{"opposed_purposes": ["Recomendaciones de lectura"]}`,
    actual `404`
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL con `assert response.status_code == 200` → `404 != 200`
  - Document counterexample: "GET /users/me/oppositions devuelve 404 porque el endpoint no existe"
  - Mark task complete when tests are written, run, and failure is documented
  - _Requirements: 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - POST /users/me/oppose behavior unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe en código SIN fix: `POST /users/me/oppose` con propósito válido devuelve `200`
    con `OpposeResponse(opposed=True)` y persiste en `privacy_settings["opposed_purposes"]`
  - Observe: registrar el mismo propósito dos veces no genera duplicados (invariante ya
    implementado en `OpposeDataProcessing`)
  - Observe: `POST` sin token devuelve `401`
  - Crear `backend/tests/test_oppose_preservation.py`
  - Usar `@given` + `@settings` de Hypothesis (patrón de `test_metadata_properties.py`)
  - **Property 2a**: para cualquier propósito `p` con 1–200 chars, `POST /users/me/oppose`
    devuelve `OpposeResponse` con `processing_purpose == p` y `opposed == True`
  - **Property 2b**: idempotencia — registrar `p` dos veces → la lista no tiene duplicados
  - **Property 2c**: sin token → `401` (no depende del fix)
  - Verify tests PASS on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirma baseline que no debe romperse)
  - _Requirements: 3.1, 3.2, 3.4_

- [x] 3. Fix: Add GET /users/me/oppositions endpoint

  - [x] 3.1 Crear `backend/app/identity/application/get_user_oppositions.py`
    - Definir `class UserNotFoundError(Exception)` local al módulo
    - Definir `class GetUserOppositions` con `__init__(self, user_repository, audit_service)`
    - Implementar `execute(self, user_id: UUID) -> list[str]`:
      - `user = self._user_repo.find_by_id(user_id)` → raise `UserNotFoundError` si es None
      - `self._audit_service.log(actor_user_id=user_id, action=AuditAction.ARCO_REQUEST,
        affected_entity=f"user:{user_id}:oppositions")` — reutilizar `ARCO_REQUEST`
        (lectura ARCO, coherente con el patrón de `ExportUserData`)
      - `return (user.privacy_settings or {}).get("opposed_purposes", [])`
    - Seguir el módulo docstring de `oppose_data_processing.py` como referencia
    - _Bug_Condition: `isBugCondition(ctx)` donde `ctx.endpoint_exists == False`_
    - _Expected_Behavior: `GET /users/me/oppositions` → `200 {"opposed_purposes": [...]}`_
    - _Requirements: 2.3_

  - [x] 3.2 Añadir `OppositionsResponse` schema en `backend/app/identity/interface/schemas.py`
    - Añadir al final de la sección `# --- ARCO Rectification & Opposition schemas ---`:
      ```python
      class OppositionsResponse(BaseModel):
          """Response body for GET /users/me/oppositions."""
          opposed_purposes: list[str]
      ```
    - _Requirements: 2.3_

  - [x] 3.3 Añadir endpoint en `backend/app/identity/interface/users_router.py`
    - Añadir imports: `GetUserOppositions` y su `UserNotFoundError` al bloque de imports
      existente (seguir el patrón del import de `OpposeDataProcessing`)
    - Añadir `OppositionsResponse` al import de `schemas`
    - Añadir handler `GET /me/oppositions` ANTES del handler `POST /me/oppose` (orden
      alfabético de método evita conflictos de routing en FastAPI):
      ```python
      @router.get("/me/oppositions", response_model=OppositionsResponse)
      def get_user_oppositions(
          current_user_id: UUID = Depends(get_current_user_id),
          db: Session = Depends(get_db),
      ):
          """List all active data processing oppositions for the authenticated user.
          ARCO opposition right — read access.
          """
      ```
    - Instanciar repos y `AuditService` igual que en los demás handlers (patrón de
      `export_user_data`)
    - `try/except UserNotFoundError → 404 "user_not_found"`
    - `db.commit()` antes del return
    - `return OppositionsResponse(opposed_purposes=purposes)`
    - _Preservation: POST /users/me/oppose permanece inalterado_
    - _Requirements: 2.3, 3.4_

  - [x] 3.4 Añadir tipo `OppositionsResponse` en `frontend/src/types/index.ts`
    - Añadir en la sección `// === Settings / Privacy ===`, junto a `OpposeRequest` y
      `OpposeResponse`:
      ```typescript
      export interface OppositionsResponse {
        opposed_purposes: string[];
      }
      ```
    - _Requirements: 2.1_

  - [x] 3.5 Actualizar `OppositionForm` en `frontend/src/app/settings/page.tsx`
    - Añadir `OppositionsResponse` al import de `@/types`
    - Añadir `apiGet` al import de `@/lib/api-client` si no está presente
    - **Estado nuevo**: `const [activeOppositions, setActiveOppositions] = useState<string[]>([])`
    - **Estado nuevo**: `const [loadingOppositions, setLoadingOppositions] = useState(true)`
    - **useEffect al montar**: fetch `GET /users/me/oppositions` con `apiGet<OppositionsResponse>`,
      guardar `data.opposed_purposes` en `activeOppositions`. Si falla, log silencioso (no
      bloquear UI principal). `finally: setLoadingOppositions(false)`
    - **Optimistic update tras submit exitoso**: en el bloque `try` de `handleSubmit`, después
      de `await apiPost(...)`, añadir `setActiveOppositions(prev => [...prev, purpose])` antes
      de `setShowConfirmation(true)`
    - **Render de la lista** (añadir ANTES del botón "Registrar oposición" / del formulario):
      - Si `loadingOppositions`: skeleton div con `animate-pulse` y `bg-gray-200 h-4 rounded`
      - Si `!loadingOppositions && activeOppositions.length === 0`: párrafo
        "No tienes oposiciones registradas aún." con `color: var(--color-ink-faint)`
      - Si `activeOppositions.length > 0`: `<ul>` con chips de solo lectura usando
        `border: "1px solid var(--color-teak)"`, `color: "var(--color-teak)"`,
        `background: "transparent"`, `rounded-full px-3 py-1 text-sm`
      - Cada chip como `<li key={purpose}><span ...>{purpose}</span></li>`
      - Añadir `aria-label="Oposiciones registradas"` al `<ul>`
    - _Bug_Condition: `ctx.ui_shows_list == False`_
    - _Preservation: chips de selección y campo libre del formulario de alta inalterados_
    - _Requirements: 2.1, 2.2_

- [x] 4. Verify bug condition exploration test now passes
  - **Property 1: Expected Behavior** - GET /users/me/oppositions returns 200 with list
  - **IMPORTANT**: Re-run the SAME tests from task 1 — do NOT write new tests
  - Run `backend/tests/test_get_user_oppositions_exploration.py`
  - **EXPECTED OUTCOME**: Tests PASS (confirma que el endpoint existe y devuelve datos correctos)
  - _Requirements: 2.3_

- [x] 5. Verify preservation tests still pass
  - **Property 2: Preservation** - POST /users/me/oppose behavior unchanged after fix
  - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
  - Run `backend/tests/test_oppose_preservation.py`
  - **EXPECTED OUTCOME**: Tests PASS (sin regresiones en el POST)
  - Confirmar que `test_arco_integration.py` existente también sigue pasando

- [x] 6. Unit tests para GetUserOppositions
  - Crear `backend/tests/test_get_user_oppositions.py` (patrón de `TestExportUserDataUseCase`
    en `test_arco_integration.py`)
  - Usar `TestSession` de `tests/conftest.py` + repos SQL reales (no mocks)
  - `test_returns_empty_list_for_user_without_oppositions`: usuario recién creado con
    `privacy_settings` vacío → `execute()` devuelve `[]`
  - `test_returns_correct_list`: usuario con `privacy_settings={"opposed_purposes": ["A", "B"]}`
    → `execute()` devuelve `["A", "B"]`
  - `test_user_not_found_raises_error`: `user_id` inexistente → raises `UserNotFoundError`
  - `test_audit_log_created_with_arco_request`: verifica que `audit_repo.find_by_actor(user_id)`
    tiene un log con `action == AuditAction.ARCO_REQUEST` y
    `f"user:{user_id}:oppositions" in logs[0].affected_entity`
  - `test_null_privacy_settings`: usuario con `privacy_settings=None` → devuelve `[]`
    (defensivo ante datos legacy)
  - _Requirements: 2.3_

- [x] 7. Integration tests para el endpoint GET /users/me/oppositions
  - Añadir clase `TestGetOppositionsEndpoint` a `backend/tests/test_arco_integration.py`
    (patrón de `TestExportEndpoint`)
  - `test_returns_empty_list_for_new_user`: register+login → `GET /users/me/oppositions`
    → `200 {"opposed_purposes": []}`
  - `test_returns_list_after_post`: register+login → `POST /users/me/oppose` con
    "Estadísticas de uso" → `GET /users/me/oppositions` → lista contiene "Estadísticas de uso"
  - `test_no_duplicates_after_double_post`: registrar el mismo propósito dos veces → lista
    tiene exactamente una ocurrencia
  - `test_requires_auth`: `GET /users/me/oppositions` sin token → `422`
  - `test_rejects_invalid_token`: token inválido → `401`
  - `test_post_still_works_after_fix`: verifica que `POST /users/me/oppose` sigue devolviendo
    `OpposeResponse` con `opposed: true` (regression guard)
  - _Requirements: 2.3, 3.1, 3.4_

- [x] 8. Checkpoint — Ensure all tests pass
  - Ejecutar `pytest backend/tests/test_get_user_oppositions.py backend/tests/test_arco_integration.py backend/tests/test_get_user_oppositions_exploration.py backend/tests/test_oppose_preservation.py -v`
  - Verificar que todos los tests pasen sin warnings de deprecación
  - Verificar que `ruff check backend/app/identity/` no reporta errores en los archivos nuevos
  - Preguntar al usuario si surgen dudas antes de proceder con el frontend

## Notes

- No hay cambios al modelo de datos ni migraciones — `privacy_settings` ya existe como campo
  `dict` en `User` y los datos están persistidos correctamente
- El nuevo endpoint reutiliza `AuditAction.ARCO_REQUEST` (lectura ARCO) — no se necesita un
  nuevo valor de enum
- El optimistic update del frontend añade el propósito localmente sin re-fetch para mantener
  la UX fluida; si el servidor rechaza el POST, el error se muestra inline y el estado local
  no se corrompe (el `setShowConfirmation` solo se ejecuta en el bloque `try` tras éxito)
- Tests frontend (Vitest + Testing Library) para `OppositionForm` están fuera del scope de este
  bugfix — el componente ya tiene cobertura en los tests de arco-profile-panel

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2"] },
    { "wave": 2, "tasks": ["3.1"] },
    { "wave": 3, "tasks": ["3.2", "3.3"] },
    { "wave": 4, "tasks": ["3.4", "3.5"] },
    { "wave": 5, "tasks": ["4", "5", "6"] },
    { "wave": 6, "tasks": ["7"] },
    { "wave": 7, "tasks": ["8"] }
  ]
}
```
