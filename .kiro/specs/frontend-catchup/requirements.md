# Requirements Document

## Introduction

This specification defines the frontend views for EntreLíneas covering all backend functionality delivered in milestones M0 through M6. The frontend is a Next.js 16 application (React 19, TypeScript, Tailwind CSS) communicating with the FastAPI backend on port 8000 via REST. CORS is already configured for localhost:3000.

The existing frontend skeleton (created in M-1) contains only a health-check page. This milestone (M6.5) delivers complete UI coverage for: authentication, family groups, library management, reading selection, clubs, reviews, and privacy basics — enabling incremental frontend delivery from M7 onward.

Privacy is a first-class concern: no content is ever "public". All sharing is explicit to a group or club, consistent with Ley 21.719 (Chile) compliance.

## Glossary

- **App**: The EntreLíneas Next.js frontend application running on port 3000.
- **API_Client**: The HTTP client module that handles all requests to the FastAPI backend (port 8000), including token attachment and refresh.
- **Auth_Module**: The frontend authentication layer responsible for login, registration, logout, and token lifecycle management.
- **Dashboard**: The authenticated landing page showing the user's library summary, recent activity, and navigation.
- **Library_View**: The set of pages for managing books and copies (list, create, search).
- **Groups_View**: The set of pages for managing family groups (create, invite, view members).
- **Selection_View**: The set of pages for reading selection (trigger draw, view history, see next picker).
- **Clubs_View**: The set of pages for managing book clubs (create, view, set active book, comments).
- **Reviews_View**: The set of pages for managing book reviews (create, list, edit, delete).
- **Settings_View**: The user settings pages for privacy actions (export data, delete account).
- **Protected_Route**: A route wrapper that redirects unauthenticated users to the login page.
- **Toast**: A non-blocking notification component for success/error feedback.

## Requirements

### Requirement 1: Authentication Pages

**User Story:** As a user, I want to log in, register, and log out of EntreLíneas, so that I can securely access my personal library data.

#### Acceptance Criteria

1. THE App SHALL provide a login page at `/login` with email and password fields.
2. WHEN valid credentials are submitted, THE Auth_Module SHALL store the access token and refresh token securely and redirect the user to the Dashboard.
3. WHEN invalid credentials are submitted, THE Auth_Module SHALL display a descriptive error message without revealing whether the email or password is incorrect.
4. THE App SHALL provide a registration page at `/register` with fields for display name, email, password, and password confirmation.
5. WHEN a registration form is submitted, THE Auth_Module SHALL require explicit consent acceptance (privacy policy acknowledgment) before calling the backend.
6. IF registration fails due to validation errors, THEN THE App SHALL display field-level error messages returned by the backend.
7. THE App SHALL provide a logout action accessible from any authenticated page that clears tokens and redirects to the login page.
8. WHILE the access token is expired, THE API_Client SHALL attempt a token refresh using the stored refresh token before failing the request.
9. IF the refresh token is also expired or revoked, THEN THE Auth_Module SHALL clear all stored tokens and redirect the user to the login page.

### Requirement 2: Protected Routes and Session Management

**User Story:** As a user, I want my data protected from unauthorized access, so that only I can see my library when logged in.

#### Acceptance Criteria

1. THE App SHALL wrap all routes except `/login` and `/register` with a Protected_Route that verifies authentication state.
2. WHEN an unauthenticated user navigates to a protected route, THE App SHALL redirect to `/login` and preserve the intended destination URL.
3. WHEN the user completes login after a redirect, THE App SHALL navigate to the originally intended destination.
4. THE App SHALL persist authentication state across page refreshes without requiring re-login (while tokens remain valid).

### Requirement 3: Dashboard

**User Story:** As a reader, I want a home page after login that shows me an overview of my library and recent activity, so that I can quickly navigate to what matters.

#### Acceptance Criteria

1. THE App SHALL provide a Dashboard page at `/dashboard` as the default authenticated landing page.
2. THE Dashboard SHALL display a summary of the user's book count and recent activity.
3. THE Dashboard SHALL provide navigation links to Library, Groups, Selection, Clubs, Reviews, and Settings sections.
4. THE Dashboard SHALL display the user's display name and provide access to logout.

### Requirement 4: Library Management

**User Story:** As a reader, I want to manage my book collection through the frontend, so that I can add books, track copies, and search my library.

#### Acceptance Criteria

1. THE App SHALL provide a library list page at `/library` that displays the user's books with title, author, and copy count.
2. THE Library_View SHALL support pagination or infinite scroll for large collections.
3. THE App SHALL provide an "Add Book" form accessible from the library page with fields for title, author, ISBN (optional), and format.
4. WHEN a book is successfully created, THE App SHALL display a Toast confirmation and add the book to the list.
5. THE Library_View SHALL allow adding a copy to an existing book, specifying format (physical or digital) and condition.
6. THE App SHALL provide a search field on the library page that filters books by title or author using the backend search endpoint.
7. IF the library is empty, THEN THE Library_View SHALL display an empty state with guidance on how to add the first book.

### Requirement 5: Family Groups Management

**User Story:** As a family member, I want to create and manage my family group, so that we can share books and reading activities together.

#### Acceptance Criteria

1. THE App SHALL provide a groups page at `/groups` that lists the user's family groups with member count.
2. THE Groups_View SHALL allow creating a new family group with a name.
3. THE Groups_View SHALL allow inviting a member to a group by email.
4. WHEN an invitation is sent successfully, THE App SHALL display a Toast confirmation.
5. THE App SHALL display pending invitations received by the current user with accept/decline actions.
6. WHEN the user accepts a group invitation, THE App SHALL update the groups list to reflect the new membership.
7. THE Groups_View SHALL display group members for each group the user belongs to.

### Requirement 6: Reading Selection

**User Story:** As a family group member, I want to trigger reading draws and see whose turn it is to pick, so that we can fairly choose our next read.

#### Acceptance Criteria

1. THE App SHALL provide a reading selection page at `/selection` accessible from the Dashboard.
2. THE Selection_View SHALL display the current picker (whose turn it is) for each group the user belongs to.
3. THE Selection_View SHALL allow triggering a filtered random draw, with optional filters for format and genre.
4. WHEN a draw is triggered, THE Selection_View SHALL display the result (selected book) with title and author.
5. THE Selection_View SHALL display the draw history for the current group, ordered by most recent.
6. IF no books match the filter criteria, THEN THE Selection_View SHALL display a message indicating no eligible books were found.

### Requirement 7: Clubs

**User Story:** As a reader, I want to participate in book clubs with reading turns and discussions, so that I can share the reading experience with others.

#### Acceptance Criteria

1. THE App SHALL provide a clubs list page at `/clubs` that displays clubs the user belongs to.
2. THE Clubs_View SHALL allow creating a new club with a name and optional description.
3. THE Clubs_View SHALL display a club detail page showing the active book, members, and current reading turn.
4. THE Clubs_View SHALL allow the club owner to set the active book from available copies.
5. THE Clubs_View SHALL display a comments section for the active book, ordered chronologically.
6. THE Clubs_View SHALL allow posting a comment on the active book.
7. WHEN a comment is posted, THE App SHALL append the comment to the list without a full page reload.
8. THE Clubs_View SHALL display a spoiler warning indicator on comments marked as containing spoilers.

### Requirement 8: Reviews

**User Story:** As a reader, I want to write reviews for books and control who sees them, so that I can record my opinions with explicit sharing choices.

#### Acceptance Criteria

1. THE App SHALL provide a reviews section accessible from the book detail or a dedicated `/reviews` page listing the user's own reviews.
2. THE Reviews_View SHALL allow creating a review with a rating (1–5 stars), optional text, and an explicit visibility choice (`private` or `shared`).
3. WHEN visibility is `shared`, THE Reviews_View SHALL require the user to select exactly which Group or Club the review is shared with.
4. THE Reviews_View SHALL NEVER default to a shared visibility — the user must always explicitly choose.
5. THE Reviews_View SHALL allow editing or deleting reviews authored by the current user.
6. THE App SHALL display reviews for a book, filtered to only those the current user is authorized to see (own reviews + reviews shared with groups/clubs the user belongs to).
7. WHEN a review is created or edited, THE App SHALL display a Toast confirmation.

### Requirement 9: User Settings and Privacy

**User Story:** As a user, I want to export my data and delete my account, so that I maintain control over my personal information per Ley 21.719.

#### Acceptance Criteria

1. THE App SHALL provide a settings page at `/settings` accessible from the Dashboard navigation.
2. THE Settings_View SHALL provide an "Export My Data" action that triggers a data export request to the backend.
3. WHEN the export is initiated, THE App SHALL display a confirmation message indicating the export is being prepared.
4. THE Settings_View SHALL provide a "Delete My Account" action with a confirmation dialog requiring explicit confirmation (e.g., typing account email).
5. WHEN account deletion is confirmed, THE Auth_Module SHALL clear all local state and redirect to the login page with a farewell message.
6. IF an export or deletion request fails, THEN THE App SHALL display a descriptive error message.

### Requirement 10: API Client and Error Handling

**User Story:** As a developer, I want a centralized API client that handles authentication headers and errors consistently, so that all pages share reliable backend communication.

#### Acceptance Criteria

1. THE API_Client SHALL attach the access token as a Bearer header to all authenticated requests.
2. WHEN a request returns HTTP 401, THE API_Client SHALL attempt a token refresh and retry the original request exactly once.
3. IF the retry also fails with 401, THEN THE API_Client SHALL trigger a logout and redirect to login.
4. WHEN a request returns HTTP 4xx (other than 401), THE API_Client SHALL propagate the error response body to the calling component for field-level display.
5. WHEN a request returns HTTP 5xx, THE API_Client SHALL display a generic Toast error indicating a server issue.
6. THE API_Client SHALL use the base URL `http://localhost:8000` configurable via environment variable (`NEXT_PUBLIC_API_URL`).

### Requirement 11: Responsive Layout and Navigation

**User Story:** As a user, I want a consistent, responsive layout across all pages, so that I can use EntreLíneas on desktop and mobile devices.

#### Acceptance Criteria

1. THE App SHALL provide a consistent navigation layout with sidebar (desktop) or bottom navigation (mobile) across all authenticated pages.
2. THE App SHALL be usable on viewports from 320px to 1920px wide.
3. THE App SHALL provide a loading skeleton or spinner while data is being fetched from the backend.
4. WHEN navigation occurs between pages, THE App SHALL indicate the active section in the navigation.
5. THE App SHALL use Tailwind CSS for all styling, consistent with the existing project configuration.
