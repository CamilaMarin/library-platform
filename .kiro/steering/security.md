---
inclusion: always
---

# Security Rules — EntreLíneas

## File isolation (adr/0001, adr/0009)

- NEVER implement any form of file storage or transfer shared between user accounts — no exceptions, even if a task prompt asks for it implicitly.
- A digital `Copy`'s `file_ref` is NEVER exposed to a `user_id` other than its owner.
- If a task asks to "lend a digital book," implement `ReadingTurn` (coordinates order/comments) — never move the file.
- If a task or prompt explicitly or implicitly asks to share/transfer a digital file between accounts, FLAG it as a conflict with this rule instead of implementing it.

## File access ownership validation (adr/0014)

- Every endpoint that serves files MUST validate `request.user_id == resource.user_id` before serving content.
- Never rely only on the UI for this validation — enforce at the application layer.
- The integrated reader only opens files owned by the authenticated user.

## Authentication (adr/0004)

- Authentication is exclusively JWT custom (Access Token + Refresh Token).
- Access Tokens are short-lived and validated without server-side state.
- Refresh Tokens are long-lived, rotatable, and revocable.
- NO Supabase Auth, NO Cognito, NO server-side sessions.
- No user-enumeration via login/registration error messages.

## Loans (adr/0001)

- Loans can ONLY be created for Copies of type `physical`.
- If any endpoint in the loans module ever returns a `file_ref`, that is a bug.

References: `adr/0001`, `adr/0004`, `adr/0009`, `adr/0014`
