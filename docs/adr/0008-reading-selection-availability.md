# ADR-0008: Reading Selection — Availability Rule

## Status
Accepted

## Context
The draw filter "availability for everyone" was ambiguous — it wasn't clear whether it meant everyone owns a copy, the copy is available (not lent out), or both.

## Decision
The "availability for everyone" rule is defined as:

> **Every selected participant must have authorized access to the chosen book.**

- For **physical books**: there must be at least one available copy (not lent out) accessible to the participant.
- For **digital books**: each participant must own their own personal copy.

## Consequences
- The draw algorithm must cross participants × copies, verifying ownership/availability per participant.
- A digital book can only enter the draw if all participants individually own it.
- A physical book can only enter if there are enough available copies or an applicable turn mechanism.
- Reinforces ADR-0001: another user's digital file is never offered as a way to satisfy "availability."
