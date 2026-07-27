"""Repository interfaces for the Circulation bounded context.

These protocols define the contract between application and infrastructure layers.
Reference: ADR-0015 (Loans reference Copies), ADR-0017 (cloud agnostic)
"""

from typing import Protocol
from uuid import UUID

from app.circulation.domain.entities import Loan
from app.library.domain.entities import Copy


class LoanRepository(Protocol):
    """Persistence interface for Loan."""

    def save(self, loan: Loan) -> Loan: ...

    def find_by_id(self, loan_id: UUID) -> Loan | None: ...

    def find_active_by_copy_id(self, copy_id: UUID) -> Loan | None: ...

    def update(self, loan: Loan) -> Loan: ...


class CopyQuery(Protocol):
    """Cross-context read interface for Copy (from Library bounded context).

    Provides read access to Copy data needed by the Circulation module.
    Reference: ADR-0015
    """

    def find_by_id(self, copy_id: UUID) -> Copy | None: ...

    def update_status(self, copy_id: UUID, status: str) -> None: ...
