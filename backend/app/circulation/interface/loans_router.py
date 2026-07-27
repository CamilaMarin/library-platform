"""Loans REST endpoints.

Reference: loans/design.md, ADR-0015, Requirements 1.1, 1.3
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.circulation.application.register_loan import RegisterLoan
from app.circulation.application.register_return import RegisterReturn
from app.circulation.infrastructure.repositories import SqlCopyQuery, SqlLoanRepository
from app.database import get_db
from app.identity.interface.dependencies import get_current_user_id

router = APIRouter(prefix="/copies", tags=["loans"])


class CreateLoanRequest(BaseModel):
    """Request body for creating a loan."""

    borrower_user_id: UUID
    estimated_return_date: datetime | None = None


class LoanResponse(BaseModel):
    """Response body for a loan."""

    id: UUID
    copy_id: UUID
    borrower_user_id: UUID
    loan_date: datetime
    estimated_return_date: datetime | None
    returned_date: datetime | None
    status: str


@router.post(
    "/{copy_id}/loans",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_loan(
    copy_id: UUID,
    request: CreateLoanRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Register a new loan for a physical copy.

    Only physical copies can be loaned (Req 1.1).
    Digital copies are rejected with 422 invalid_copy_type (Req 1.3).
    """
    loan_repository = SqlLoanRepository(db)
    copy_query = SqlCopyQuery(db)
    use_case = RegisterLoan(loan_repository=loan_repository, copy_query=copy_query)

    try:
        loan = use_case.execute(
            copy_id=copy_id,
            borrower_user_id=request.borrower_user_id,
            estimated_return_date=request.estimated_return_date,
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "invalid_copy_type":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="invalid_copy_type",
            )
        elif error_msg == "copy_already_on_loan":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="copy_already_on_loan",
            )
        elif error_msg == "Copy not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Copy not found",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

    db.commit()

    return LoanResponse(
        id=loan.id,
        copy_id=loan.copy_id,
        borrower_user_id=loan.borrower_user_id,
        loan_date=loan.loan_date,
        estimated_return_date=loan.estimated_return_date,
        returned_date=loan.returned_date,
        status=loan.status.value,
    )


# --- Return endpoint (separate prefix for /loans/{id}) ---

return_router = APIRouter(prefix="/loans", tags=["loans"])


@return_router.patch("/{loan_id}/return", response_model=LoanResponse)
def return_loan(
    loan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark a loan as returned, reverting copy status to available.

    Idempotent: returning an already-returned loan returns 200 with current state.
    Reference: loans/design.md Property 4, Requirements 1.2
    """
    loan_repository = SqlLoanRepository(db)
    copy_query = SqlCopyQuery(db)
    use_case = RegisterReturn(loan_repository=loan_repository, copy_query=copy_query)

    try:
        loan = use_case.execute(loan_id=loan_id)
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "Loan not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

    db.commit()

    return LoanResponse(
        id=loan.id,
        copy_id=loan.copy_id,
        borrower_user_id=loan.borrower_user_id,
        loan_date=loan.loan_date,
        estimated_return_date=loan.estimated_return_date,
        returned_date=loan.returned_date,
        status=loan.status.value,
    )
