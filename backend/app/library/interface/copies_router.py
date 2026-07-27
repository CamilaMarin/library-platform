"""Copies REST endpoints.

Reference: library/tasks.md#3, #4, ADR-0001, ADR-0009, ADR-0015
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.interface.dependencies import get_current_user_id
from app.library.application.create_copy import (
    CreateCopy,
    CreateDigitalCopyRequest,
    CreatePhysicalCopyRequest,
)
from app.library.infrastructure.file_storage import LocalFileStorage
from app.library.infrastructure.repositories import SqlBookRepository, SqlCopyRepository
from app.library.interface.schemas import CopyResponse

router = APIRouter(prefix="/copies", tags=["copies"])


class ActiveLoanInfo(BaseModel):
    """Active loan info for a copy."""

    borrower_name: str
    loan_date: str


class CopyWithLoanStatusResponse(BaseModel):
    """Copy with loan status information."""

    id: UUID
    book_id: UUID
    user_id: UUID
    format: str
    filename: str | None
    created_at: str
    loan_status: str
    active_loan: ActiveLoanInfo | None = None


@router.get("/", response_model=list[CopyWithLoanStatusResponse])
def list_copies_with_loan_status(
    book_id: UUID | None = Query(default=None, description="Filter by book ID"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List copies for the authenticated user with loan status.

    Optionally filter by book_id. Returns copies with their current
    loan status (available or on_loan) and active loan details.
    Never exposes file_ref per ADR-0009.
    Reference: Requirements 5.1, 5.4
    """
    from app.circulation.infrastructure.models import LoanModel
    from app.identity.infrastructure.models import UserModel
    from app.library.infrastructure.models import CopyModel

    query = db.query(CopyModel).filter(CopyModel.user_id == UUID(user_id))

    if book_id:
        query = query.filter(CopyModel.book_id == book_id)

    copies = query.all()

    results = []
    for copy in copies:
        loan_status = "available"
        active_loan = None

        if copy.type == "physical":
            # Check for active loan on this copy
            active_loan_model = (
                db.query(LoanModel)
                .filter(LoanModel.copy_id == copy.id, LoanModel.status == "active")
                .first()
            )
            if active_loan_model:
                loan_status = "on_loan"
                borrower = (
                    db.query(UserModel)
                    .filter(UserModel.id == active_loan_model.borrower_user_id)
                    .first()
                )
                active_loan = ActiveLoanInfo(
                    borrower_name=borrower.name if borrower else "Desconocido",
                    loan_date=active_loan_model.loan_date.isoformat(),
                )

        results.append(CopyWithLoanStatusResponse(
            id=copy.id,
            book_id=copy.book_id,
            user_id=copy.user_id,
            format=copy.type,
            filename=None,  # Never expose file_ref per ADR-0009
            created_at=copy.created_at.isoformat(),
            loan_status=loan_status,
            active_loan=active_loan,
        ))

    return results


@router.post("/physical", response_model=CopyResponse, status_code=status.HTTP_201_CREATED)
def create_physical_copy(
    book_id: UUID = Form(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a physical copy (metadata + status only, no file)."""
    use_case = CreateCopy(
        copy_repository=SqlCopyRepository(db),
        book_repository=SqlBookRepository(db),
    )

    try:
        copy = use_case.create_physical(
            CreatePhysicalCopyRequest(book_id=book_id, user_id=UUID(user_id))
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    db.commit()
    return CopyResponse.from_copy(copy)


@router.post("/digital", response_model=CopyResponse, status_code=status.HTTP_201_CREATED)
async def create_digital_copy(
    book_id: UUID = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a digital copy with encrypted file upload.

    Accepts EPUB and PDF files only. Max 50MB.
    File is stored in per-user isolated storage (ADR-0009).
    """
    content = await file.read()

    use_case = CreateCopy(
        copy_repository=SqlCopyRepository(db),
        book_repository=SqlBookRepository(db),
        file_storage=LocalFileStorage(),
    )

    try:
        copy = use_case.create_digital(
            CreateDigitalCopyRequest(
                book_id=book_id,
                user_id=UUID(user_id),
                filename=file.filename or "unknown.pdf",
                content=content,
            )
        )
    except ValueError as e:
        error_msg = str(e)
        if "Unsupported file format" in error_msg or "File too large" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "unsupported_file", "message": error_msg},
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)

    db.commit()
    return CopyResponse.from_copy(copy)


@router.delete("/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_copy(
    copy_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a copy. Only the owner can delete. Removes file if digital."""
    from app.library.application.delete_copy import DeleteCopy

    use_case = DeleteCopy(
        copy_repository=SqlCopyRepository(db),
        file_storage=LocalFileStorage(),
    )

    try:
        use_case.execute(copy_id=copy_id, user_id=UUID(user_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    db.commit()
