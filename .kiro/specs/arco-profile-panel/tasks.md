# Implementation Plan: ARCO Profile Panel

## Overview

Refactor the existing Settings page to complete all 4 ARCO rights: add profile editing (rectification), replace the incomplete export with a real JSON download (access), add an opposition form, and reorganize the page into Profile and ARCO sections. All work is frontend-only — the backend endpoints already exist. Implementation follows a foundation-first approach: pure utilities and types first, then auth context enhancement, then UI components, with property-based tests validating correctness properties throughout.

## Tasks

- [x] 1. Foundation: Types, validation utilities, and export utility
  - [x] 1.1 Add RectifyRequest, RectifyResponse, OpposeRequest, OpposeResponse types to `frontend/src/types/index.ts`
    - Add the four interfaces as defined in the design document
    - Keep them grouped under the existing `// === Settings / Privacy ===` section
    - _Requirements: 1.3, 3.3_

  - [x] 1.2 Create `frontend/src/lib/settings-validation.ts` with pure validation functions
    - Implement `validateName(name: string): string | null`
    - Implement `validateEmail(email: string): string | null`
    - Implement `validatePurpose(purpose: string): string | null`
    - Implement `isRectificationFormValid(name: string, email: string): boolean`
    - Implement `isOppositionFormValid(purpose: string): boolean`
    - Follow validation rules from design: name 1–200 chars trimmed, email regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` max 320 chars, purpose 1–200 chars trimmed
    - _Requirements: 1.8, 3.7_

  - [x] 1.3 Create `frontend/src/lib/export-download.ts` with download utility functions
    - Implement `generateExportFilename(): string` returning `entrelineas-datos-YYYY-MM-DD.json`
    - Implement `triggerJsonDownload(data: unknown, filename: string): void` using Blob + URL.createObjectURL + programmatic `<a>` click + URL.revokeObjectURL
    - _Requirements: 2.2, 2.5_

- [x] 2. Auth Context enhancement
  - [x] 2.1 Add `updateUser` method to `frontend/src/context/auth-context.tsx`
    - Extend `AuthContextValue` interface with `updateUser(fields: Partial<Pick<UserInfo, "name" | "email">>): void`
    - Implement as a `useCallback` that merges fields into current user state and persists via `storeUserInfo`
    - Must NOT modify tokens (access_token, refresh_token remain untouched)
    - Is synchronous — no API call, just state + localStorage update
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 3. Property-based tests for foundation utilities
  - [x] 3.1 Write property test for rectification form validation (Property 1)
    - **Property 1: Rectification form validation correctly classifies inputs**
    - Generate arbitrary strings for name and email using fast-check
    - Assert: `isRectificationFormValid` returns true iff name.trim().length in [1,200] AND email matches pattern with length ≤ 320
    - **Validates: Requirements 1.3, 1.8**

  - [x] 3.2 Write property test for auth state synchronization (Property 2)
    - **Property 2: Auth state synchronization after rectification**
    - Generate arbitrary valid name/email pairs
    - Assert: after `updateUser`, both context state and localStorage contain those exact values while preserving user.id
    - **Validates: Requirements 1.4, 6.1**

  - [x] 3.3 Write property test for token preservation (Property 3)
    - **Property 3: Token preservation after profile update**
    - Generate arbitrary valid name/email pairs and pre-set arbitrary token values
    - Assert: after `updateUser`, token storage is unchanged
    - **Validates: Requirements 6.3**

  - [x] 3.4 Write property test for export file generation (Property 4)
    - **Property 4: Export file generation round-trip**
    - Generate arbitrary JSON-serializable objects matching ExportData shape
    - Assert: Blob content parsed back as JSON is deeply equal to original, filename matches `entrelineas-datos-YYYY-MM-DD.json` pattern
    - **Validates: Requirements 2.2**

  - [x] 3.5 Write property test for opposition form validation (Property 5)
    - **Property 5: Opposition form validation correctly classifies inputs**
    - Generate arbitrary strings for purpose
    - Assert: `isOppositionFormValid` returns true iff purpose.trim().length in [1,200]
    - **Validates: Requirements 3.3, 3.7**

- [x] 4. Checkpoint - Ensure foundation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Settings page refactor: Profile Section with Rectification Form
  - [x] 5.1 Refactor `frontend/src/app/settings/page.tsx` — page structure and Profile Section
    - Restructure page into two visually distinct card sections: Profile_Section (top) and ARCO_Section (below)
    - Implement ProfileSection with display mode showing current name and email from Auth_Context
    - Implement edit toggle that shows RectificationForm with pre-filled inputs
    - Use "sala de lectura" design tokens: walnut headings, cream/parchment backgrounds, Playfair Display for section headings, rounded-button style
    - Add `aria-label` on inputs, `aria-describedby` linking errors to inputs, `role="alert"` on error messages, `role="status"` on success messages
    - Mobile-first responsive layout from 320px up to desktop
    - _Requirements: 1.1, 1.2, 4.1, 4.2, 5.1, 5.2, 5.3, 5.4_

  - [x] 5.2 Implement Rectification Form submission logic
    - Call client-side validation (`validateName`, `validateEmail`) on blur and before submit
    - Send PATCH to `/users/me` with changed fields using `apiPatch`
    - On success: update displayed values, call `updateUser` on Auth_Context, show success toast
    - On 409: inline error "Este correo ya está en uso" on email field
    - On 400 `invalid_email_format`: inline error "Formato de correo inválido"
    - On 400 `no_fields_provided`: inline error "Debes modificar al menos un campo"
    - Disable submit button + show loading text while submitting
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 6.1, 6.2_

- [x] 6. Settings page: Export download
  - [x] 6.1 Replace export section with real download implementation
    - Replace the existing "export is being prepared" message with actual file download
    - On click: call `GET /users/me/export`, then call `triggerJsonDownload` with response data and `generateExportFilename()`
    - Show loading state on button while request is in progress
    - On error: show inline error with "Reintentar" button
    - Remove the old success message that says "Tu exportación se está preparando"
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 7. Settings page: Opposition Form
  - [x] 7.1 Implement Opposition Form in ARCO Section
    - Add opposition action button that reveals the form when activated
    - Display predefined purposes as clickable chips: "Recomendaciones de lectura", "Estadísticas de uso", "Comunicaciones no esenciales"
    - Include free text input for custom purpose
    - Validate purpose with `validatePurpose` before enabling submission
    - Send POST to `/users/me/oppose` with purpose string
    - On success: show confirmation message and reset form
    - On error: show inline error message
    - Disable submit button + loading indicator while submitting
    - Add `aria-label` on input, `aria-describedby` for errors
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 7.2 Add ARCO Section legal information and rights grouping
    - Group all four ARCO rights with clear labels: Acceso (export), Rectificación (reference to Profile Section), Cancelación (delete), Oposición (form)
    - Include brief legal explanation referencing Ley 21.719
    - Ensure existing delete account section remains unchanged in behavior
    - Full keyboard navigation: all elements reachable via Tab, activatable via Enter/Space
    - _Requirements: 4.3, 4.4, 4.5, 5.4_

- [x] 8. Checkpoint - Ensure all components render and basic flows work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Integration tests and regression
  - [x] 9.1 Write integration tests for Settings page
    - Test full page render with mocked API calls
    - Test rectification happy path: edit → submit → context updated → display updated
    - Test export happy path: click → download triggered
    - Test opposition happy path: select purpose → submit → confirmation shown
    - Test error scenarios: 409, 400, network errors
    - Test keyboard navigation through all interactive elements
    - _Requirements: 1.1–1.8, 2.1–2.5, 3.1–3.7, 4.1–4.5, 5.3, 5.4_

  - [x] 9.2 Write regression test for delete account flow
    - Verify delete account flow still works after page refactoring
    - Test email confirmation + delete API call + redirect to login
    - _Requirements: 4.5_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- All implementation uses TypeScript + React + Tailwind + Vitest + fast-check
- No backend work needed — all endpoints exist (`PATCH /users/me`, `POST /users/me/oppose`, `GET /users/me/export`, `DELETE /users/me`)
- The `apiPatch` helper may need to be added to `frontend/src/lib/api-client.ts` if it doesn't already exist (follow existing `apiPost`/`apiGet`/`apiDelete` patterns)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5"] },
    { "id": 3, "tasks": ["5.1", "6.1"] },
    { "id": 4, "tasks": ["5.2", "7.1", "7.2"] },
    { "id": 5, "tasks": ["9.1", "9.2"] }
  ]
}
```
