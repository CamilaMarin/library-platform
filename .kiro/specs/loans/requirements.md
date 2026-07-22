# Requirements Document

## Introduction

This module records physical-book loans between people. Loans exist only for physical copies; digital sharing is out of scope by design.

Source: `docs/domain/business-rules.md` (rule 2).

### Referenced ADRs
- `adr/0001-no-shared-file-storage.md` — No file sharing between accounts
- `adr/0009-digital-books-isolation.md` — Digital books strict isolation
- `adr/0015-book-copy-separation.md` — Book/Copy separation (loans reference Copies, not Books)

## Glossary

- **Loan**: record that a physical Copy is temporarily in another person's possession. Never applies to digital copies.

## Requirements

### Requirement 1: Loans between people

**User Story:** As a reader, I want to record when I lend a physical book to someone, so I know where each copy in my library is.

#### Acceptance Criteria
1. THE SYSTEM SHALL allow recording loans only for copies of type "physical".
2. WHEN a physical copy is on loan, THE SYSTEM SHALL mark it with status `on_loan` and allow an optional estimated return date.
3. THE SYSTEM SHALL NOT offer transfer of, or temporary access to, a digital file between different accounts under any concept of "loan".
