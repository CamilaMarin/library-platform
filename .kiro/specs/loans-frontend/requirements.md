# Requirements Document

## Introduction

This module adds frontend pages to the EntreLíneas Next.js 16 application for the Loans feature (M7). The backend is already complete with endpoints for creating loans (`POST /copies/{id}/loans`) and marking returns (`PATCH /loans/{id}/return`). This spec covers the user-facing interface: viewing loans, creating loans from physical copies, returning loans, and displaying loan status in the library.

All UI text is in Spanish. Only physical copies participate in loans — digital copies and file references are never surfaced in loan-related interfaces.

### Referenced ADRs
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation
- `adr/0015-book-copy-separation.md` — Loans reference Copies (not Books)

## Glossary

- **Loans_Page**: The dedicated frontend page at `/loans` showing active and historical loans for the authenticated user.
- **Loan_Card**: A UI component displaying a single loan's information (book title, borrower, dates, status).
- **Loan_Form**: The form component for registering a new loan, selecting a borrower from group members.
- **Library_Page**: The existing `/library` page showing the user's books and copies.
- **Copy_Status_Badge**: A visual indicator on a copy showing its current loan status.
- **Toast_System**: The existing notification system for success/error feedback.
- **API_Client**: The existing centralized HTTP client module with automatic token handling.
- **Navigation**: The existing sidebar/bottom-bar navigation component.

## Requirements

### Requirement 1: Loans Page — Active Loans View

**User Story:** As a user, I want to see my active loans (books I have lent out) in a dedicated page, so that I can track which physical copies are currently with other people.

#### Acceptance Criteria

1. THE Navigation SHALL include a "Préstamos" link pointing to `/loans` in both desktop sidebar and mobile bottom bar.
2. WHEN the user navigates to `/loans`, THE Loans_Page SHALL fetch and display all active loans for the authenticated user.
3. THE Loans_Page SHALL display each active loan as a Loan_Card showing: book title, borrower name, loan date, and estimated return date (if set).
4. WHILE the Loans_Page is loading data, THE Loans_Page SHALL display skeleton placeholders.
5. IF the user has no active loans, THEN THE Loans_Page SHALL display an empty state message: "No tienes préstamos activos."
6. THE Loans_Page SHALL be a protected route requiring authentication.

### Requirement 2: Loans Page — Loan History View

**User Story:** As a user, I want to see my past returned loans, so that I can keep a record of lending activity.

#### Acceptance Criteria

1. THE Loans_Page SHALL provide a way to view returned loans separately from active loans (tab or section toggle).
2. WHEN the user switches to the history view, THE Loans_Page SHALL display returned loans with: book title, borrower name, loan date, and returned date.
3. IF the user has no returned loans, THEN THE Loans_Page SHALL display an empty state message: "No tienes préstamos devueltos."

### Requirement 3: Create Loan

**User Story:** As a user, I want to register a loan for a physical copy to a member of my group, so that I can track who has my book.

#### Acceptance Criteria

1. WHEN viewing a physical copy in the Library_Page, THE Library_Page SHALL display a "Prestar" action button for copies with status `available`.
2. WHEN the user clicks the "Prestar" button, THE Loan_Form SHALL appear allowing selection of a borrower from the user's group members.
3. THE Loan_Form SHALL include an optional estimated return date field.
4. WHEN the user submits the Loan_Form, THE API_Client SHALL call `POST /copies/{copy_id}/loans` with `borrower_user_id` and optional `estimated_return_date`.
5. WHEN the loan creation succeeds (HTTP 201), THE Toast_System SHALL display "Préstamo registrado" and the copy status SHALL update to reflect the active loan.
6. IF the backend returns HTTP 409 (copy already on loan), THEN THE Toast_System SHALL display "Esta copia ya está prestada."
7. IF the backend returns HTTP 422 (invalid copy type), THEN THE Toast_System SHALL display "Solo se pueden prestar copias físicas."
8. WHILE the Loan_Form is submitting, THE Loan_Form submit button SHALL be disabled and show a loading indicator.

### Requirement 4: Return Loan

**User Story:** As a user, I want to mark a loan as returned from the loans list, so that the copy is recorded as available again.

#### Acceptance Criteria

1. WHEN viewing an active loan in the Loans_Page, THE Loan_Card SHALL display a "Marcar devuelto" button.
2. WHEN the user clicks "Marcar devuelto", THE API_Client SHALL call `PATCH /loans/{loan_id}/return`.
3. WHEN the return succeeds (HTTP 200), THE Toast_System SHALL display "Préstamo devuelto" and the loan SHALL move from active to history.
4. IF the backend returns HTTP 404 (loan not found), THEN THE Toast_System SHALL display "Préstamo no encontrado."
5. WHILE the return request is in progress, THE "Marcar devuelto" button SHALL be disabled and show a loading indicator.

### Requirement 5: Loan Status in Library

**User Story:** As a user, I want to see loan status on my copies in the library page, so that I know at a glance which copies are lent out and to whom.

#### Acceptance Criteria

1. WHEN the Library_Page displays copies for a book, THE Library_Page SHALL show a Copy_Status_Badge for each physical copy indicating whether the copy is available or on loan.
2. WHILE a copy is on loan, THE Copy_Status_Badge SHALL display the borrower's name and the loan date.
3. WHILE a copy is on loan, THE Library_Page SHALL NOT display the "Prestar" action for that copy.
4. THE Library_Page SHALL fetch copy loan status alongside copy data.

### Requirement 6: Privacy — No Digital Copy Information in Loans UI

**User Story:** As a user, I want the loans interface to only show physical copies, so that digital file information is never exposed in a lending context.

#### Acceptance Criteria

1. THE Loans_Page SHALL NOT display any loan associated with a digital copy.
2. THE Library_Page SHALL NOT display the "Prestar" action button for copies with format `digital`.
3. THE Loan_Form SHALL NOT include any field for file references or digital file paths.
4. THE Loans_Page SHALL NOT render `filename`, `file_ref`, or any digital-copy-specific field in any loan display.
