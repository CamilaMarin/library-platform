"""Repository implementations for the Circulation bounded context.

Implements protocols from application/protocols.py.
Reference: ADR-0015, ADR-0017
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.circulation.domain.entities import Loan, LoanStatus
from app.circulation.infrastructure.models import LoanModel
from app.library.domain.entities import Copy, CopyStatus, CopyType
from app.library.infrastructure.models import CopyModel


class SqlLoanRepository:
    """SQLAlchemy implementation of LoanRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, loan: Loan) -> Loan:
        model = LoanModel(
            id=loan.id,
            copy_id=loan.copy_id,
            borrower_user_id=loan.borrower_user_id,
            loan_date=loan.loan_date,
            estimated_return_date=loan.estimated_return_date,
            returned_date=loan.returned_date,
            status=loan.status.value,
        )
        self._session.add(model)
        self._session.flush()
        return loan

    def find_by_id(self, loan_id: UUID) -> Loan | None:
        model = self._session.get(LoanModel, loan_id)
        if not model:
            return None
        return self._to_domain(model)

    def find_active_by_copy_id(self, copy_id: UUID) -> Loan | None:
        model = (
            self._session.query(LoanModel)
            .filter(LoanModel.copy_id == copy_id, LoanModel.status == "active")
            .first()
        )
        if not model:
            return None
        return self._to_domain(model)

    def update(self, loan: Loan) -> Loan:
        model = self._session.get(LoanModel, loan.id)
        if model:
            model.status = loan.status.value
            model.returned_date = loan.returned_date
            model.estimated_return_date = loan.estimated_return_date
            self._session.flush()
        return loan

    def _to_domain(self, model: LoanModel) -> Loan:
        return Loan(
            id=model.id,
            copy_id=model.copy_id,
            borrower_user_id=model.borrower_user_id,
            loan_date=model.loan_date,
            estimated_return_date=model.estimated_return_date,
            returned_date=model.returned_date,
            status=LoanStatus(model.status),
        )


class SqlCopyQuery:
    """SQLAlchemy implementation of CopyQuery.

    Cross-context read from Library tables. Does NOT import Library's
    application layer — only reads from the shared database models.
    Reference: ADR-0015
    """

    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, copy_id: UUID) -> Copy | None:
        model = self._session.get(CopyModel, copy_id)
        if not model:
            return None
        return Copy(
            id=model.id,
            user_id=model.user_id,
            book_id=model.book_id,
            type=CopyType(model.type),
            file_ref=model.file_ref,
            status=CopyStatus(model.status),
        )

    def update_status(self, copy_id: UUID, status: str) -> None:
        model = self._session.get(CopyModel, copy_id)
        if model:
            model.status = status
            self._session.flush()
