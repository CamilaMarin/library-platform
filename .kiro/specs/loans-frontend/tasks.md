# Implementation Plan: Loans Frontend (M7 UI)

## Overview

Incrementally build the loans management UI: start with types and backend GET endpoint, then new components, the loans page, library page modifications, and finally navigation wiring. Property-based tests validate correctness properties from the design.

## Tasks

- [x] 1. Add Loan types and backend GET endpoint
  - [x] 1.1 Add Loan types to `src/types/index.ts`
    - Add `Loan`, `LoanWithDetails`, `CreateLoanRequest`, and `CopyWithLoanStatus` interfaces
    - Add `GroupMember` interface for borrower selection
    - _Requirements: 1.3, 2.2, 3.4, 5.1_

  - [x] 1.2 Add `GET /loans` endpoint to backend
    - Create a new route in `app/circulation/interface/loans_router.py` that accepts `?status=active|returned`
    - Return loans for the authenticated user with denormalized `book_title` and `borrower_name`
    - Add repository method to query loans by owner and status
    - _Requirements: 1.2, 2.1_

- [x] 2. Implement new components
  - [x] 2.1 Create `CopyStatusBadge` component (`src/components/copy-status-badge.tsx`)
    - Render green "Disponible" badge for `available` status
    - Render orange "Prestado a {borrowerName}" badge with loan date for `on_loan` status
    - _Requirements: 5.1, 5.2_

  - [x] 2.2 Create `LoanCard` component (`src/components/loan-card.tsx`)
    - Accept `LoanCardProps` with `variant` ("active" | "returned")
    - Active variant: show book title, borrower name, loan date, estimated return date, and "Marcar devuelto" button
    - Returned variant: show book title, borrower name, loan date, returned date (no action button)
    - Handle loading state on "Marcar devuelto" button
    - Never render `file_ref`, `filename`, or file path strings
    - _Requirements: 1.3, 2.2, 4.1, 4.5, 6.4_

  - [x] 2.3 Create `LoanForm` component (`src/components/loan-form.tsx`)
    - Dropdown to select borrower from group members
    - Optional estimated return date input
    - Submit calls `POST /copies/{copyId}/loans` via API client
    - Disable submit button during request, show "Registrando..." text
    - Show success toast "Préstamo registrado" and call `onSuccess` on 201
    - Show error toasts for 409 and 422 responses
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 6.3_

- [x] 3. Implement Loans page
  - [x] 3.1 Create `src/app/loans/page.tsx` with tabs and data fetching
    - Wrap in `ProtectedRoute`
    - Two tabs: "Activos" (default) and "Historial"
    - Fetch `GET /loans?status=active` for Activos tab, `GET /loans?status=returned` for Historial tab
    - Render list of `LoanCard` components with appropriate variant
    - Implement `onReturn` handler calling `PATCH /loans/{id}/return`, show toast, refresh list
    - Handle 404 error on return with correct toast message
    - Show skeleton placeholders while loading
    - Show empty state messages: "No tienes préstamos activos." / "No tienes préstamos devueltos."
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 4.1, 4.2, 4.3, 4.4, 6.1, 6.4_

- [x] 4. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Modify Library page for loan integration
  - [x] 5.1 Add loan status display and "Prestar" button to Library page (`src/app/library/page.tsx`)
    - Fetch copy loan status alongside copy data
    - Display `CopyStatusBadge` for each physical copy
    - Show "Prestar" button only for physical copies with `loan_status === "available"`
    - Hide "Prestar" for digital copies and copies on loan
    - On "Prestar" click, show `LoanForm` inline; fetch group members for borrower dropdown
    - On successful loan creation, update copy status in UI
    - _Requirements: 3.1, 3.2, 5.1, 5.2, 5.3, 5.4, 6.2_

- [x] 6. Add navigation link
  - [x] 6.1 Add "Préstamos" link to navigation (`src/components/navigation.tsx`)
    - Add to both `desktopNavItems` and `mobileNavItems` with href `/loans` and icon "🔄"
    - _Requirements: 1.1_

- [x] 7. Property-based and unit tests
  - [x] 7.1 Write property test for "Prestar" button visibility (Property 1)
    - **Property 1: "Prestar" button visibility**
    - Generate arbitrary copy objects with fast-check; assert button appears iff `format === "physical"` AND `loan_status === "available"`
    - Minimum 100 iterations
    - **Validates: Requirements 3.1, 5.3, 6.2**

  - [x] 7.2 Write property test for LoanCard required fields (Property 2)
    - **Property 2: Loan card renders all required fields for its status**
    - Generate arbitrary `LoanWithDetails` objects; assert active variant renders book title, borrower, loan date, estimated return date (when present); returned variant renders book title, borrower, loan date, returned date
    - Minimum 100 iterations
    - **Validates: Requirements 1.3, 2.2**

  - [x] 7.3 Write property test for no file references in loan display (Property 3)
    - **Property 3: No file references in loan display**
    - Generate arbitrary loan objects with random `file_ref` and `filename` fields injected; assert rendered output never contains those values
    - Minimum 100 iterations
    - **Validates: Requirements 6.1, 6.4**

  - [x] 7.4 Write unit tests for LoanForm, CopyStatusBadge, and navigation
    - Test LoanForm submits correct payload, handles errors with correct toasts
    - Test CopyStatusBadge renders correct text/colors for each status
    - Test navigation includes "Préstamos" link in desktop and mobile
    - _Requirements: 1.1, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2_

- [x] 8. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The backend GET /loans endpoint (task 1.2) is a prerequisite for the loans page — if it already exists, skip it
- Property tests use `fast-check` (already in devDependencies) with React Testing Library
- All UI text is in Spanish per project conventions
- Digital copies are never shown in loan contexts (privacy requirement per ADRs 0001, 0009)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["5.1", "6.1"] },
    { "id": 4, "tasks": ["7.1", "7.2", "7.3", "7.4"] }
  ]
}
```
