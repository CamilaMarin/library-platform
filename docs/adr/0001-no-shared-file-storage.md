# ADR-0001: No Storing or Transferring Copyrighted Files Between Accounts

## Status
Accepted

## Context
The project needs to allow users to manage their own digital books (EPUB/PDF) and coordinate joint reading in family clubs. There is real legal risk: sharing digital access to a copyrighted file between different people generally constitutes infringement of reproduction/distribution rights — even the "controlled digital lending" model (one digital copy per physical copy owned) was found to be infringement by the U.S. Second Circuit Court of Appeals in *Hachette v. Internet Archive* (2024).

## Decision
- Every digital file uploaded by a user is isolated to that account, encrypted, with no transfer or concurrent access mechanism by another account, under any circumstance.
- "Loans" apply only to physical copies (a social/logistical record, no file involved).
- Joint reading coordination for a digital book is solved with the "reading turn" concept, which requires each participant to own their own copy.

## Consequences
- An attractive-sounding feature ("lend my EPUB to my sister") is deliberately sacrificed to avoid legal exposure.
- The model aligns with Calibre/Komga/Kavita (isolated personal library), not with a public-library-style lending system.
- Reinforces the product principle "the user always owns their library."
