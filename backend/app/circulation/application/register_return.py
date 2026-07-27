"""RegisterReturn use case — marks a loan as returned and reverts copy status.

Reference: loans/design.md, Property 4, Requirements 1.2
"""

from datetime import datetime, timezone
from uuid import UUID

from app.circulation.application.protocols import CopyQuery, LoanRepository
from app.circulation.domain.entities import Loan, LoanStatus


class RegisterReturn:
    """Use case: register the return of a loaned copy.

    Enforces:
    - Loan must exist
    - Copy status reverts to 'available' (Property 4)
    - Idempotent: returning an already-returned loan is a no-op (200)
    """

    def __init__(self, loan_repository: LoanRepository, copy_query: CopyQuery):
        self._loan_repository = loan_repository
        self._copy_query = copy_query

    def execute(self, loan_id: UUID) -> Loan:
        """Mark a loan as returned.

        Raises:
            ValueError("Loan not found") — loan does not exist
        """
        loan = self._loan_repository.find_by_id(loan_id)
        if loan is None:
            raise ValueError("Loan not found")

        # Idempotent: already returned → just return current state
        if loan.status == LoanStatus.RETURNED:
            return loan

        # Mark as returned
        loan.status = LoanStatus.RETURNED
        loan.returned_date = datetime.now(timezone.utc)

        self._loan_repository.update(loan)
        self._copy_query.update_status(loan.copy_id, "available")

        return loan
