# Implementation Plan: Frontend Catchup (M6.5)

## Overview

This plan implements the complete EntreLíneas Next.js 16 frontend covering authentication, family groups, library management, reading selection, clubs, reviews, and privacy/settings. Each task builds incrementally — starting with the foundational API client and auth layer, then building feature pages on top. TypeScript, React 19, Tailwind CSS, and the App Router are used throughout.

## Tasks

- [x] 1. Set up project infrastructure and shared modules
  - [x] 1.1 Create TypeScript type definitions
    - Create `src/types/index.ts` with all shared interfaces: `LoginResponse`, `RegisterRequest`, `UserInfo`, `Book`, `CreateBookRequest`, `Copy`, `FamilyGroup`, `GroupMembership`, `Draw`, `NextPicker`, `RunDrawRequest`, `Review`, `CreateReviewRequest`, `ExportData`, `ApiError`
    - _Requirements: 10.1, 10.4_

  - [x] 1.2 Implement token storage module
    - Create `src/lib/token-storage.ts` with `getAccessToken`, `getRefreshToken`, `setTokens`, `clearTokens`, `decodeTokenPayload` functions
    - Use `localStorage` for persistence; `decodeTokenPayload` base64-decodes JWT payload without verification
    - _Requirements: 1.2, 1.8, 2.4_

  - [x] 1.3 Implement API client module
    - Create `src/lib/api-client.ts` with typed functions: `apiGet<T>`, `apiPost<T>`, `apiPatch<T>`, `apiDelete`, `apiPostForm<T>`
    - Read `NEXT_PUBLIC_API_URL` env var (default `http://localhost:8000`)
    - Attach Bearer token from `token-storage` on all requests
    - On 401: attempt refresh via `POST /auth/refresh`, store new tokens, retry original request once
    - On refresh failure: clear tokens, redirect to `/login`
    - On 4xx (non-401): throw `ApiError` with parsed response body
    - On 5xx: trigger toast with generic server error message
    - On network error: trigger toast with connection error message
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 1.4 Set up testing infrastructure
    - Install dev dependencies: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `fast-check`, `msw`, `jsdom`
    - Create `vitest.config.ts` with jsdom environment and path aliases
    - Create `src/__tests__/setup.ts` with MSW server setup, jest-dom matchers, and test utilities
    - _Requirements: 10.1, 10.2_

  - [x]* 1.5 Write property tests for API client (Properties 1–5)
    - **Property 1: Bearer token attachment** — For any request when access token exists, Authorization header must equal `Bearer {token}`
    - **Property 2: Token refresh and retry on 401** — For any 401 response, client calls refresh and retries exactly once
    - **Property 3: Failed refresh triggers logout** — When refresh also fails, client clears tokens and redirects to `/login`
    - **Property 4: Client error propagation** — For any 4xx (non-401), error body is propagated unchanged
    - **Property 5: Server error toast** — For any 5xx, a toast notification is triggered
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 1.8, 1.9, 1.6**

- [x] 2. Implement auth context and toast system
  - [x] 2.1 Create Toast context and component
    - Create `src/context/toast-context.tsx` with `ToastProvider` and `useToast` hook
    - Create `src/components/toast.tsx` rendering stacked toasts (bottom-right desktop, bottom-center mobile)
    - Toasts auto-dismiss after 4 seconds; support `success`, `error`, `info` types
    - _Requirements: 4.4, 5.4, 8.7, 10.5_

  - [x] 2.2 Create Auth context
    - Create `src/context/auth-context.tsx` with `AuthProvider` and `useAuth` hook
    - Implement `AuthState` with `isAuthenticated`, `user`, `isLoading`
    - On mount: check localStorage for tokens, decode user info from payload, set authenticated state
    - Implement `login(email, password)`: call `POST /auth/login`, store tokens, set state
    - Implement `register(data)`: call `POST /auth/register`, redirect to login on success (no auto-login)
    - Implement `logout()`: call `POST /auth/logout`, clear tokens, redirect to `/login`
    - _Requirements: 1.2, 1.7, 1.8, 1.9, 2.4_

  - [x] 2.3 Create ProtectedRoute component
    - Create `src/components/protected-route.tsx`
    - Check `AuthContext`; if unauthenticated, redirect to `/login?redirect={currentPath}`
    - Show loading skeleton while `isLoading` is true
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 2.4 Write property tests for ProtectedRoute (Properties 6–7)
    - **Property 6: Protected route redirect with destination preservation** — For any path not `/login` or `/register`, unauthenticated users redirect to `/login?redirect={originalPath}`
    - **Property 7: Post-login redirect consumption** — For any valid redirect param, after auth the user navigates to that stored path
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 3. Implement shared UI components and root layout
  - [x] 3.1 Create shared form components
    - Create `src/components/input-field.tsx` — text/email/password input with label, error display, placeholder
    - Create `src/components/select-field.tsx` — dropdown with label, options, error display
    - Create `src/components/star-rating.tsx` — interactive 1–5 star picker with readonly mode
    - Create `src/components/confirm-dialog.tsx` — modal for destructive actions with title, message, confirm/cancel
    - Create `src/components/skeleton.tsx` — loading placeholders with variants: card, list, text
    - _Requirements: 11.3, 1.1, 1.4, 8.2_

  - [x] 3.2 Create Navigation component
    - Create `src/components/navigation.tsx`
    - Desktop (≥768px): fixed left sidebar (w-64) with icon + text links to Dashboard, Library, Groups, Selection, Clubs, Reviews, Settings; user name and logout at bottom
    - Mobile (<768px): fixed bottom bar with 5 icon tabs (Dashboard, Library, Clubs, Reviews, Settings)
    - Highlight active section via `usePathname()`
    - _Requirements: 11.1, 11.2, 11.4, 3.3_

  - [x] 3.3 Create root layout and providers
    - Update `src/app/layout.tsx` as Server Component with html, body, metadata
    - Wrap children with `AuthProvider` and `ToastProvider` (client boundary)
    - Create `src/app/page.tsx` that redirects to `/dashboard` if authenticated, `/login` if not
    - _Requirements: 2.1, 11.1, 11.5_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement authentication pages
  - [ ] 5.1 Create Login page
    - Create `src/app/login/page.tsx` as client component
    - Form fields: email, password, submit button
    - Client-side validation: required fields, email format
    - On submit: call `auth.login()`, handle errors with field-level display
    - On success: redirect to `redirect` query param or `/dashboard`
    - Map backend errors to Spanish messages using `ERROR_MESSAGES` map
    - _Requirements: 1.1, 1.2, 1.3, 2.3_

  - [ ] 5.2 Create Registration page
    - Create `src/app/register/page.tsx` as client component
    - Form fields: display name, email, password, password confirmation, consent checkbox
    - Client-side validation: required fields, email format, passwords match, consent checked
    - Consent checkbox must be explicitly accepted before submission
    - On submit: call `auth.register()`, on success redirect to `/login` with success toast
    - On failure: display field-level errors from backend
    - _Requirements: 1.4, 1.5, 1.6_

  - [ ]* 5.3 Write unit tests for auth pages
    - Test login page renders correct fields and labels
    - Test successful login stores tokens and redirects
    - Test invalid login shows generic error message
    - Test registration requires all fields and consent
    - Test registration displays backend validation errors
    - Use MSW to mock `/auth/login` and `/auth/register` endpoints
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [ ] 6. Implement Dashboard page
  - [ ] 6.1 Create Dashboard page
    - Create `src/app/dashboard/page.tsx` wrapped with ProtectedRoute
    - Fetch and display user's book count summary
    - Display navigation cards/links to Library, Groups, Selection, Clubs, Reviews, Settings
    - Show user display name with logout action
    - Show loading skeletons while fetching data
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 11.3_

  - [ ]* 6.2 Write unit tests for Dashboard
    - Test dashboard renders summary information
    - Test navigation links are present and functional
    - Test user name and logout are displayed
    - Test loading skeleton appears while data fetches
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 7. Implement Library Management page
  - [ ] 7.1 Create Library page
    - Create `src/app/library/page.tsx` wrapped with ProtectedRoute
    - Fetch and display books list with title, author, copy count
    - Implement pagination or infinite scroll for large collections
    - Implement search field that filters via backend search endpoint
    - Display empty state with guidance when no books exist
    - Show loading skeletons while fetching
    - _Requirements: 4.1, 4.2, 4.6, 4.7, 11.3_

  - [ ] 7.2 Implement Add Book and Add Copy functionality
    - Add "Add Book" form/modal with fields: title, author, ISBN (optional), genres, description, pages
    - On successful creation: show toast confirmation, add book to list without full reload
    - Add "Add Copy" action on existing books with format selection (physical/digital)
    - _Requirements: 4.3, 4.4, 4.5_

  - [ ]* 7.3 Write unit tests for Library page
    - Test book list renders with correct data
    - Test search filters books by title/author
    - Test add book form submits correctly and updates list
    - Test empty state displays when no books
    - Test pagination/scroll loads more items
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [ ] 8. Implement Family Groups page
  - [ ] 8.1 Create Groups page
    - Create `src/app/groups/page.tsx` wrapped with ProtectedRoute
    - Fetch and display user's family groups with member count
    - Implement "Create Group" form with name field
    - Implement "Invite Member" action with email field per group
    - Show toast on successful invitation
    - Display pending invitations received by user with accept/decline buttons
    - On accept: update groups list to reflect new membership
    - Display group members list for each group
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 8.2 Write unit tests for Groups page
    - Test groups list renders with member counts
    - Test create group form works
    - Test invite member shows toast on success
    - Test pending invitations display with actions
    - Test accept invitation updates groups list
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement Reading Selection page
  - [ ] 10.1 Create Selection page
    - Create `src/app/selection/page.tsx` wrapped with ProtectedRoute
    - Fetch and display current picker (whose turn) for each group
    - Implement draw trigger form with optional filters: genre, max pages, unread only
    - Display draw result (selected book title and author) after successful draw
    - Display draw history for current group, ordered by most recent
    - Show message when no books match filter criteria
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 10.2 Write unit tests for Selection page
    - Test current picker displays correctly
    - Test draw trigger with filters works
    - Test draw result shows book info
    - Test draw history renders in order
    - Test empty filter results show appropriate message
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 11. Implement Clubs pages
  - [ ] 11.1 Create Clubs list page
    - Create `src/app/clubs/page.tsx` wrapped with ProtectedRoute
    - Fetch and display clubs the user belongs to
    - Implement "Create Club" form with name and optional description
    - _Requirements: 7.1, 7.2_

  - [ ] 11.2 Create Club detail page
    - Create `src/app/clubs/[id]/page.tsx` wrapped with ProtectedRoute
    - Display active book, members list, and current reading turn
    - Allow club owner to set active book from available copies
    - Display comments section for active book, ordered chronologically
    - Implement comment posting form; append new comment without full page reload
    - Display spoiler warning indicator on spoiler-marked comments
    - _Requirements: 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

  - [ ]* 11.3 Write unit tests for Clubs pages
    - Test clubs list renders correctly
    - Test create club form submits successfully
    - Test club detail shows active book and members
    - Test comment posting appends to list
    - Test spoiler indicator displays
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

- [ ] 12. Implement Reviews page
  - [ ] 12.1 Create Reviews page
    - Create `src/app/reviews/page.tsx` wrapped with ProtectedRoute
    - Fetch and display user's own reviews with book title, rating, and visibility
    - Implement create review form: star rating (1–5), optional text, visibility selector (private/shared)
    - Visibility MUST NOT default to "shared" — always default to private or unselected
    - When "shared" is selected: show target selector requiring selection of exactly one Group or Club
    - Reject form submission if shared is selected without a target
    - Allow editing and deleting reviews authored by current user
    - Show toast on successful create/edit
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [ ]* 12.2 Write property tests for Reviews form (Properties 8–9)
    - **Property 8: Review visibility never defaults to shared** — For any initial render of the review form, visibility is never pre-selected to "shared"
    - **Property 9: Shared review requires explicit target** — For any submission with visibility "shared", form rejects unless exactly one target (Group or Club) is selected
    - **Validates: Requirements 8.3, 8.4**

  - [ ]* 12.3 Write unit tests for Reviews page
    - Test reviews list renders with ratings and visibility
    - Test create review form with star rating interaction
    - Test visibility defaults to private
    - Test shared visibility requires target selection
    - Test edit and delete actions work
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.7_

- [ ] 13. Implement Settings page
  - [ ] 13.1 Create Settings page
    - Create `src/app/settings/page.tsx` wrapped with ProtectedRoute
    - Implement "Export My Data" button that calls backend export endpoint
    - Show confirmation message when export is initiated
    - Implement "Delete My Account" button that opens ConfirmDialog
    - Require user to type their exact email to enable the delete action
    - On confirmed deletion: clear all local state, redirect to `/login` with farewell message
    - Display descriptive error messages if export or deletion fails
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ]* 13.2 Write property test for Settings (Property 10)
    - **Property 10: Account deletion requires exact email confirmation** — For any string that does not exactly match the user's email, the delete action remains disabled
    - **Validates: Requirements 9.4**

  - [ ]* 13.3 Write unit tests for Settings page
    - Test export button triggers request and shows confirmation
    - Test delete account requires exact email match
    - Test deletion clears state and redirects
    - Test error messages display on failure
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document (Properties 1–10)
- Unit tests validate specific examples, edge cases, and interaction flows
- All UI text is in Spanish (the target audience)
- The API client module is the foundation — all pages depend on it
- MSW is used to mock backend responses in tests, avoiding real API calls during testing

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "1.4"] },
    { "id": 2, "tasks": ["1.5", "2.1"] },
    { "id": 3, "tasks": ["2.2"] },
    { "id": 4, "tasks": ["2.3", "3.1"] },
    { "id": 5, "tasks": ["2.4", "3.2", "3.3"] },
    { "id": 6, "tasks": ["5.1", "5.2"] },
    { "id": 7, "tasks": ["5.3", "6.1"] },
    { "id": 8, "tasks": ["6.2", "7.1"] },
    { "id": 9, "tasks": ["7.2", "8.1"] },
    { "id": 10, "tasks": ["7.3", "8.2", "10.1"] },
    { "id": 11, "tasks": ["10.2", "11.1"] },
    { "id": 12, "tasks": ["11.2", "12.1"] },
    { "id": 13, "tasks": ["11.3", "12.2", "12.3", "13.1"] },
    { "id": 14, "tasks": ["13.2", "13.3"] }
  ]
}
```
