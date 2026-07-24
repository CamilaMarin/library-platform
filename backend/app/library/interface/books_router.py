"""Books REST endpoints.

Reference: library/tasks.md#2, ADR-0015
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.interface.dependencies import get_current_user_id
from app.library.application.create_book import CreateBook
from app.library.application.create_book import CreateBookRequest as CreateBookInput
from app.library.infrastructure.repositories import SqlBookRepository
from app.library.interface.schemas import BookResponse, CreateBookRequest

router = APIRouter(prefix="/books", tags=["books"])


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    request: CreateBookRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new book (metadata only, no copy). Requires authentication."""
    repo = SqlBookRepository(db)
    use_case = CreateBook(book_repository=repo)

    book = use_case.execute(
        request=CreateBookInput(
            title=request.title,
            author=request.author,
            genres=request.genres,
            description=request.description,
            pages=request.pages,
            isbn=request.isbn,
        ),
        user_id=user_id,
    )

    db.commit()

    return BookResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        genres=book.genres,
        description=book.description,
        pages=book.pages,
        isbn=book.isbn,
        created_at=book.created_at,
    )
