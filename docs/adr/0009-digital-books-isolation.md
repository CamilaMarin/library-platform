# ADR-0009: Digital Books — Strict Isolation

## Status
Accepted

## Context
Complements and reinforces ADR-0001 with specific operational decisions for the MVP.

## Decision
- EntreLíneas **never redistributes** copyrighted digital books.
- Uploaded EPUB/PDF files remain **strictly private** to the user who uploaded them.
- Shared libraries (visible to the group) expose **metadata only**, never files.
- The integrated reader only opens files belonging to the currently authenticated user.
- **No file-sharing functionality will exist in the MVP.**

## Consequences
- The download/reader endpoint validates `request.user_id == copy.user_id` as an absolute invariant.
- The group's shared library is a metadata catalog — never a repository of files accessible by others.
- Aligns with the legal position in *Hachette v. Internet Archive* and with the user ownership principle.
