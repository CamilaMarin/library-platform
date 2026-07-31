"""Copies REST endpoints.

Reference: library/tasks.md#3, #4, ADR-0001, ADR-0009, ADR-0015
Reference: reader/requirements.md Req 1.1, 1.2, 1.3, 1.5
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.interface.dependencies import get_current_user_id
from app.library.application.create_copy import (
    CreateCopy,
    CreateDigitalCopyRequest,
    CreatePhysicalCopyRequest,
)
from app.library.application.open_reader import OpenReader
from app.library.application.save_reading_progress import (
    SaveReadingProgress,
    SaveReadingProgressRequest,
)
from app.library.domain.entities import FileFormat
from app.library.infrastructure.file_storage import LocalFileStorage
from app.library.infrastructure.repositories import (
    SqlBookRepository,
    SqlCopyRepository,
    SqlReadingProgressRepository,
    SqlReadingStatusRepository,
)
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


class CreatePhysicalCopyBody(BaseModel):
    """Request body for creating a physical copy."""

    book_id: UUID


class SaveProgressRequest(BaseModel):
    """Request body for PUT /copies/{copy_id}/progress."""

    position: str = Field(..., min_length=1, max_length=1000)
    percentage: float = Field(..., ge=0.0, le=1.0)
    file_format: str = Field(..., pattern="^(epub|pdf)$")


class ReadingProgressResponse(BaseModel):
    """Response for reading progress."""

    id: UUID
    user_id: UUID
    copy_id: UUID
    position: str
    file_format: str
    percentage: float
    last_read_at: str

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[CopyWithLoanStatusResponse])
def list_copies_with_loan_status(
    book_id: UUID | None = Query(default=None, description="Filter by book ID"),
    user_id: UUID = Depends(get_current_user_id),
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

    query = db.query(CopyModel).filter(CopyModel.user_id == user_id)

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
    body: CreatePhysicalCopyBody,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a physical copy (metadata + status only, no file)."""
    use_case = CreateCopy(
        copy_repository=SqlCopyRepository(db),
        book_repository=SqlBookRepository(db),
    )

    try:
        copy = use_case.create_physical(
            CreatePhysicalCopyRequest(book_id=body.book_id, user_id=user_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    db.commit()
    return CopyResponse.from_copy(copy)


@router.post("/digital", response_model=CopyResponse, status_code=status.HTTP_201_CREATED)
async def create_digital_copy(
    book_id: UUID = Form(...),
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
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
                user_id=user_id,
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


@router.get("/{copy_id}/progress", response_model=ReadingProgressResponse)
def get_reading_progress(
    copy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieve the last saved reading position for a copy.

    Returns 200 with progress data if progress exists.
    Returns 404 if user owns the copy but no progress has been saved yet.
    Returns 403 if user doesn't own the copy.
    Reference: .kiro/specs/reader/requirements.md Req 2.2
    """
    from app.library.application.get_reading_progress import GetReadingProgress

    use_case = GetReadingProgress(
        copy_repository=SqlCopyRepository(db),
        reading_progress_repository=SqlReadingProgressRepository(db),
    )

    try:
        progress = use_case.execute(copy_id=copy_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reading progress found for this copy",
        )

    return ReadingProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        copy_id=progress.copy_id,
        position=progress.position,
        file_format=progress.file_format.value,
        percentage=progress.percentage,
        last_read_at=progress.last_read_at.isoformat(),
    )


@router.get("/{copy_id}")
def get_copy_detail(
    copy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get copy details for the authenticated owner.

    Security: Returns 403 for non-owned copies (never 404).
    Never exposes file_ref in the response (ADR-0009).
    """
    copy_repo = SqlCopyRepository(db)
    copy = copy_repo.find_by_id(copy_id)

    if copy is None or copy.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Determine format from file_ref extension (never expose file_ref itself)
    file_format = "unknown"
    if copy.file_ref:
        if copy.file_ref.endswith(".epub"):
            file_format = "epub"
        elif copy.file_ref.endswith(".pdf"):
            file_format = "pdf"
    elif copy.type.value == "physical":
        file_format = "physical"

    return {
        "id": str(copy.id),
        "book_id": str(copy.book_id),
        "format": file_format if copy.type.value == "digital" else "physical",
        "type": copy.type.value,
        "status": copy.status.value,
        "created_at": copy.created_at.isoformat(),
    }


@router.delete("/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_copy(
    copy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a copy. Only the owner can delete. Removes file if digital."""
    from app.library.application.delete_copy import DeleteCopy

    use_case = DeleteCopy(
        copy_repository=SqlCopyRepository(db),
        file_storage=LocalFileStorage(),
    )

    try:
        use_case.execute(copy_id=copy_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    db.commit()


def _content_type_for_file_ref(file_ref: str) -> str:
    """Determine content type from file reference extension.

    Only EPUB and PDF are supported digital formats.
    """
    if file_ref.endswith(".epub"):
        return "application/epub+zip"
    elif file_ref.endswith(".pdf"):
        return "application/pdf"
    # Default to octet-stream for unknown extensions
    return "application/octet-stream"


@router.get("/{copy_id}/file")
def get_copy_file(
    copy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Serve the digital file to the authenticated owner.

    Security:
    - Returns 403 for non-owned copies (never 404, to avoid leaking existence).
    - Never exposes file_ref in the response — only serves content.
    - Validates ownership at the application layer (ADR-0014).

    Reference: reader/requirements.md Req 1.1, 1.2, 1.3, 1.5
    Reference: Design Property 1 (Ownership gate)
    """
    use_case = OpenReader(
        copy_repository=SqlCopyRepository(db),
        file_storage=LocalFileStorage(),
    )

    try:
        file_content = use_case.execute(
            copy_id=copy_id,
            request_user_id=user_id,
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_copy_type", "message": str(e)},
        )
    except FileNotFoundError:
        # File missing from storage — internal error, not user-facing
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File unavailable. Please contact support.",
        )

    # Determine content type from the copy's file_ref
    # (safe — we already validated ownership above)
    copy = SqlCopyRepository(db).find_by_id(copy_id)
    if copy and copy.file_ref:
        content_type = _content_type_for_file_ref(copy.file_ref)
    else:
        content_type = "application/octet-stream"

    # TODO: Replace with StreamingResponse using a stream() method on FileStorage
    # for large files. MVP uses full bytes via Response which is acceptable.
    return Response(
        content=file_content,
        media_type=content_type,
        headers={"Content-Disposition": "inline"},
    )


@router.put("/{copy_id}/progress", response_model=ReadingProgressResponse)
def save_reading_progress(
    copy_id: UUID,
    body: SaveProgressRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Save or update reading progress for a digital copy.

    Auth required. Upserts progress for the (user, copy) pair.
    Returns 403 if user doesn't own the copy.
    Returns 422 if copy is physical or position format is invalid.

    Reference: reader/requirements.md Req 2.1, 2.3
    Reference: Design Property 2 (Progress isolation), Property 3 (Idempotent save)
    """
    use_case = SaveReadingProgress(
        copy_repository=SqlCopyRepository(db),
        reading_progress_repository=SqlReadingProgressRepository(db),
        reading_status_repository=SqlReadingStatusRepository(db),
        book_repository=SqlBookRepository(db),
    )

    try:
        progress = use_case.execute(
            SaveReadingProgressRequest(
                copy_id=copy_id,
                user_id=user_id,
                position=body.position,
                percentage=body.percentage,
                file_format=FileFormat(body.file_format),
            )
        )
    except ValueError as e:
        error_msg = str(e)
        if "owned by the user" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        # Invalid position format or physical copy
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_progress", "message": error_msg},
        )

    db.commit()
    return ReadingProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        copy_id=progress.copy_id,
        position=progress.position,
        file_format=progress.file_format.value,
        percentage=progress.percentage,
        last_read_at=progress.last_read_at.isoformat(),
    )
