"""RegisterLoan use case — creates a loan for a physical copy.

Reference: loans/design.md, ADR-0015, Requirements 1.1, 1.3
"""

from datetime import datetime
from uuid import UUID

from app.circulation.application.protocols import CopyQuery, LoanRepository
from app.circulation.domain.entities import Loan


class RegisterLoan:
    """Use case: register a new loan for a physical copy.

    Enforces:
    - Copy must exist
    - Copy must be physical (Property 1)
    - Copy must not already be on active loan (Property 2)
    - Copy status transitions to on_loan (Property 3)
    """

    def __init__(self, loan_repository: LoanRepository, copy_query: CopyQuery):
        self._loan_repository = loan_repository
        self._copy_query = copy_query

    def execute(
        self,
        copy_id: UUID,
        borrower_user_id: UUID,
        estimated_return_date: datetime | None = None,
    ) -> Loan:
        """Create a loan for the given copy.

        Raises:
            ValueError("Copy not found") — copy does not exist (404)
            ValueError("invalid_copy_type") — copy is not physical (422)
            ValueError("copy_already_on_loan") — copy has an active loan (409)
        """
        copy = self._copy_query.find_by_id(copy_id)
        if copy is None:
            raise ValueError("Copy not found")

        if copy.type.value != "physical":
            raise ValueError("invalid_copy_type")

        active_loan = self._loan_repository.find_active_by_copy_id(copy_id)
        if active_loan is not None:
            raise ValueError("copy_already_on_loan")

        loan = Loan.create(
            copy_id=copy_id,
            copy_type=copy.type.value,
            borrower_user_id=borrower_user_id,
            estimated_return_date=estimated_return_date,
        )

        loan = self._loan_repository.save(loan)
        self._copy_query.update_status(copy_id, "on_loan")

        return loan
