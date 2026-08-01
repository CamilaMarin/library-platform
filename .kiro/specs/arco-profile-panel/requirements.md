# Requirements Document

## Introduction

The Settings page (`/settings`) currently only implements Export (incomplete — shows a message but never delivers the file) and Delete Account. The privacy policy (`/privacy`) promises all 4 ARCO rights (Acceso, Rectificación, Cancelación, Oposición) per Chile's Ley 21.719, but Rectification and Opposition have no UI. This feature completes the ARCO panel by adding an editable profile section, a working JSON export download, an opposition form, and reorganizing the Settings page to clearly separate profile management from ARCO rights.

All backend endpoints already exist (`PATCH /users/me`, `POST /users/me/oppose`, `GET /users/me/export`, `DELETE /users/me`). This is primarily a frontend feature.

## Glossary

- **Settings_Page**: The authenticated `/settings` route in the Next.js frontend that hosts profile editing and ARCO rights actions.
- **Profile_Section**: The UI area within Settings_Page where the user views and edits their name and email.
- **ARCO_Section**: The UI area within Settings_Page where the user exercises their four ARCO rights (Access, Rectification, Cancellation, Opposition).
- **Export_Action**: The mechanism that calls `GET /users/me/export` and delivers the response as a downloadable JSON file in the browser.
- **Rectification_Form**: The inline form within Profile_Section that allows the user to edit their name and email via `PATCH /users/me`.
- **Opposition_Form**: The UI form within ARCO_Section that allows the user to register opposition to a data processing purpose via `POST /users/me/oppose`.
- **Auth_Context**: The React context that provides the current authenticated user's info (id, name, email) to the frontend.

## Requirements

### Requirement 1: Profile Display and Edit (Rectification)

**User Story:** As a registered user, I want to view and edit my name and email from the Settings page, so that I can exercise my ARCO rectification right and keep my personal data accurate.

#### Acceptance Criteria

1. WHEN the Settings_Page loads, THE Profile_Section SHALL display the current user name and email retrieved from Auth_Context.
2. WHEN the user activates the edit mode in Profile_Section, THE Rectification_Form SHALL display pre-filled input fields for name and email.
3. WHEN the user submits Rectification_Form with a valid name (1–200 characters) and a valid email, THE Settings_Page SHALL send a PATCH request to `/users/me` with the changed fields.
4. WHEN the backend returns a successful rectification response, THE Profile_Section SHALL update the displayed name and email, update Auth_Context, and show a success notification.
5. IF the backend returns a 409 conflict (email already taken), THEN THE Rectification_Form SHALL display an inline error message indicating the email is already in use.
6. IF the backend returns a 400 error (invalid email format or no fields provided), THEN THE Rectification_Form SHALL display an inline error message describing the validation failure.
7. WHILE Rectification_Form is submitting, THE submit button SHALL be disabled and display a loading indicator.
8. THE Rectification_Form SHALL validate that the name field is not empty and the email field matches a basic email pattern before enabling submission (client-side pre-validation).

### Requirement 2: Data Export (Access) as Downloadable File

**User Story:** As a registered user, I want to download a JSON file containing all my personal data, so that I can exercise my ARCO access right and receive a portable copy of my information.

#### Acceptance Criteria

1. WHEN the user activates the export button in ARCO_Section, THE Export_Action SHALL send a GET request to `/users/me/export`.
2. WHEN the backend returns the export JSON payload, THE Export_Action SHALL trigger a browser file download with filename `entrelineas-datos-{date}.json` where `{date}` is the current date in ISO format (YYYY-MM-DD).
3. WHILE the export request is in progress, THE export button SHALL be disabled and display a loading state.
4. IF the export request fails, THEN THE ARCO_Section SHALL display an inline error message with a retry option.
5. THE Export_Action SHALL NOT display a generic "data is being prepared" message — the download SHALL be delivered immediately from the API response.

### Requirement 3: Opposition to Data Processing

**User Story:** As a registered user, I want to register my opposition to specific data processing purposes, so that I can exercise my ARCO opposition right as guaranteed by Ley 21.719.

#### Acceptance Criteria

1. WHEN the user activates the opposition action in ARCO_Section, THE Opposition_Form SHALL be displayed with a text input for the processing purpose the user opposes.
2. THE Opposition_Form SHALL provide selectable predefined purposes (e.g., "Recomendaciones de lectura", "Estadísticas de uso", "Comunicaciones no esenciales") to guide the user, while also allowing free text input.
3. WHEN the user submits Opposition_Form with a purpose string (1–200 characters), THE Settings_Page SHALL send a POST request to `/users/me/oppose` with the purpose.
4. WHEN the backend returns a successful opposition response, THE Opposition_Form SHALL display a confirmation message and reset the form.
5. IF the opposition request fails, THEN THE Opposition_Form SHALL display an inline error message.
6. WHILE Opposition_Form is submitting, THE submit button SHALL be disabled and display a loading indicator.
7. THE Opposition_Form SHALL validate that the purpose field is not empty before enabling submission.

### Requirement 4: Settings Page Organization

**User Story:** As a registered user, I want the Settings page to clearly separate my profile information from my data rights actions, so that I can easily find and exercise each ARCO right.

#### Acceptance Criteria

1. THE Settings_Page SHALL be divided into two visually distinct sections: Profile_Section (top) and ARCO_Section (below).
2. THE Profile_Section SHALL contain the user's current name and email display, and the Rectification_Form.
3. THE ARCO_Section SHALL group all four ARCO rights with clear labels: Acceso (export), Rectificación (link/reference to Profile_Section), Cancelación (delete account), and Oposición (opposition form).
4. THE ARCO_Section SHALL include a brief explanation referencing Ley 21.719 to inform users of their legal rights.
5. THE Settings_Page SHALL maintain the existing delete account functionality without behavioral changes.

### Requirement 5: Design System and Accessibility Compliance

**User Story:** As a user on any device, I want the Settings page to follow the platform's visual identity and accessibility standards, so that the experience is consistent and usable.

#### Acceptance Criteria

1. THE Settings_Page SHALL use the "sala de lectura" design tokens: walnut for headings, cream/parchment for backgrounds, Playfair Display for section headings, and the existing rounded-button style for actions.
2. THE Settings_Page SHALL be responsive with a mobile-first layout that works from 320px viewport width up to desktop.
3. THE Rectification_Form and Opposition_Form SHALL include appropriate `aria-label` attributes on all inputs and `role="alert"` or `role="status"` on feedback messages.
4. THE Settings_Page SHALL support full keyboard navigation: all interactive elements SHALL be reachable via Tab and activatable via Enter or Space.
5. THE Settings_Page SHALL display form validation errors adjacent to the relevant input field with `aria-describedby` linking the error to its input.

### Requirement 6: Auth Context Synchronization

**User Story:** As a user who just edited my profile, I want the rest of the application to immediately reflect my updated name and email, so that my identity is consistent across the platform.

#### Acceptance Criteria

1. WHEN a successful rectification response is received, THE Settings_Page SHALL update the user information stored in Auth_Context and in localStorage.
2. WHEN Auth_Context is updated after rectification, THE Navigation component SHALL reflect the new user name without requiring a page reload.
3. THE Auth_Context update SHALL preserve the user's authenticated session (tokens remain valid after profile edit).
