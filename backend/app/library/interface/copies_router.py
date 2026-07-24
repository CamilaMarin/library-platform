"""Copies REST endpoints.

Reference: library/tasks.md#3, ADR-0001, ADR-0009, ADR-0015
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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
