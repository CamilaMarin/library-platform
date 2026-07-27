"""Books REST endpoints.

Reference: library/tasks.md#2, #4, ADR-0015
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.interface.dependencies import get_current_user_id
from app.library.application.create_book import CreateBook
from app.library.application.create_book import CreateBookRequest as CreateBookInput
from app.library.application.delete_book import BookHasCopiesError, DeleteBook
from app.library.application.edit_book import EditBook, EditBookRequest
from app.library.application.search_books import SearchBooks
from app.library.infrastructure.repositories import SqlBookRepository
from app.library.interface.schemas import BookResponse, CreateBookRequest, UpdateBookRequest

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


@router.get("/", response_model=list[BookResponse])
def search_books(
    query: str = "",
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Search books in personal and group library. Metadata only, never file_ref."""
    repo = SqlBookRepository(db)
    use_case = SearchBooks(book_repository=repo)

    # TODO: get group member IDs from user's groups for shared library search
    # For now, search personal library only
    books = use_case.execute(query=query, user_id=user_id)

    return [
        BookResponse(
            id=b.id,
            title=b.title,
            author=b.author,
            genres=b.genres,
            description=b.description,
            pages=b.pages,
            isbn=b.isbn,
            created_at=b.created_at,
        )
        for b in books
    ]


@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: UUID,
    request: UpdateBookRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a book's metadata. Requires authentication."""
    repo = SqlBookRepository(db)
    use_case = EditBook(book_repository=repo)

    try:
        book = use_case.execute(
            EditBookRequest(
                book_id=book_id,
                title=request.title,
                author=request.author,
                genres=request.genres,
                description=request.description,
                pages=request.pages,
                isbn=request.isbn,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

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


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a book. Returns 409 if copies still exist."""
    repo = SqlBookRepository(db)
    use_case = DeleteBook(book_repository=repo)

    try:
        use_case.execute(book_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BookHasCopiesError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    db.commit()
