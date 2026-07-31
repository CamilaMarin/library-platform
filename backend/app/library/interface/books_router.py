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
from app.library.application.get_reading_statuses import GetReadingStatuses
from app.library.application.protocols import MetadataProviderError
from app.library.application.search_book_metadata import (
    InvalidIsbnError,
    SearchBookMetadata,
    SearchBookMetadataRequest,
)
from app.library.application.search_books import SearchBooks
from app.library.application.set_reading_status import SetReadingStatus, SetReadingStatusRequest
from app.library.infrastructure.open_library_adapter import OpenLibraryAdapter
from app.library.infrastructure.repositories import (
    SqlBookRepository,
    SqlCopyRepository,
    SqlReadingStatusRepository,
)
from app.library.interface.schemas import (
    BookMetadataResponse,
    BookResponse,
    CreateBookRequest,
    ReadingStatusResponse,
    UpdateBookRequest,
)
from app.library.interface.schemas import (
    SetReadingStatusRequest as SetReadingStatusSchema,
)

router = APIRouter(prefix="/books", tags=["books"], redirect_slashes=False)


# ── Reading Status endpoints — MUST be declared before /{book_id} routes ─────
# FastAPI matches routes in declaration order. /statuses would be captured by
# /{book_id} as a UUID if declared after it, causing 422 (ADR pattern).

@router.get("/statuses", response_model=list[ReadingStatusResponse])
def get_reading_statuses(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return all (book_id, status) pairs for the authenticated user.

    Property 3: only returns records where user_id == caller (never another user's).
    """
    repo = SqlReadingStatusRepository(db)
    use_case = GetReadingStatuses(reading_status_repository=repo)
    records = use_case.execute(user_id=user_id)
    return [
        ReadingStatusResponse(
            book_id=r.book_id,
            status=r.status,
            current_page=r.current_page,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.get("/metadata/search", response_model=list[BookMetadataResponse])
def search_book_metadata(
    query: str,
    type: str = "text",
    user_id: UUID = Depends(get_current_user_id),
):
    """Search external sources for book metadata (autocomplete).

    Privacy: only transmits the query string to external APIs.
    No user identifiers are sent. No responses are persisted.
    """
    adapter = OpenLibraryAdapter()
    use_case = SearchBookMetadata(metadata_provider=adapter)

    try:
        results = use_case.execute(
            SearchBookMetadataRequest(query=query, search_type=type)
        )
    except InvalidIsbnError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_isbn_format",
        )
    except MetadataProviderError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="external_metadata_service_unavailable",
        )

    return [
        BookMetadataResponse(
            title=r.title,
            author=r.author,
            genres=r.genres,
            description=r.description,
            pages=r.pages,
            isbn=r.isbn,
        )
        for r in results
    ]


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    request: CreateBookRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new book (metadata only, no copy). Requires authentication.

    If initial_copy_format is None or 'none', creates the book without a copy
    and automatically sets reading status to 'want_to_read' so it appears
    in the library shelf view.
    """
    repo = SqlBookRepository(db)
    copy_repo = SqlCopyRepository(db)
    use_case = CreateBook(book_repository=repo, copy_repository=copy_repo)

    # Treat explicit "none" the same as no copy
    copy_format = request.initial_copy_format
    if copy_format == "none":
        copy_format = None

    book = use_case.execute(
        request=CreateBookInput(
            title=request.title,
            author=request.author,
            genres=request.genres,
            description=request.description,
            pages=request.pages,
            isbn=request.isbn,
            initial_copy_format=copy_format,
        ),
        user_id=user_id,
    )

    # If created without a copy, auto-tag as want_to_read so it appears in library
    if not copy_format:
        from app.library.domain.entities import ReadingStatusValue
        status_repo = SqlReadingStatusRepository(db)
        SetReadingStatus(
            reading_status_repository=status_repo,
            book_repository=repo,
        ).execute(
            SetReadingStatusRequest(
                user_id=user_id,
                book_id=book.id,
                status=ReadingStatusValue.WANT_TO_READ,
            )
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

    if not query.strip():
        # No query — list all user's books (only books where user owns a copy)
        books = repo.find_by_user_copies(user_id)
    else:
        # Search with query term
        use_case = SearchBooks(book_repository=repo)
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


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a single book by ID. Metadata only, never file_ref."""
    repo = SqlBookRepository(db)
    book = repo.find_by_id(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="book_not_found")

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


# ── Reading Status endpoints (PUT / DELETE) ───────────────────────────────────


@router.put("/{book_id}/status", response_model=ReadingStatusResponse)
def set_reading_status(
    book_id: UUID,
    request: SetReadingStatusSchema,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upsert reading status for a book.

    Accepts: want_to_read | reading | read | dnf
    Property 2: only affects the record for the authenticated user.
    """
    book_repo = SqlBookRepository(db)
    status_repo = SqlReadingStatusRepository(db)
    use_case = SetReadingStatus(
        reading_status_repository=status_repo,
        book_repository=book_repo,
    )

    try:
        record = use_case.execute(
            SetReadingStatusRequest(
                user_id=user_id,
                book_id=book_id,
                status=request.status,
                current_page=request.current_page,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    db.commit()
    return ReadingStatusResponse(
        book_id=record.book_id,
        status=record.status,
        current_page=record.current_page,
        updated_at=record.updated_at,
    )


@router.delete("/{book_id}/status", status_code=status.HTTP_204_NO_CONTENT)
def delete_reading_status(
    book_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove reading status for a book. Idempotent — 204 even if not set.

    Property 2: only deletes the record for the authenticated user.
    """
    repo = SqlReadingStatusRepository(db)
    repo.delete(user_id=user_id, book_id=book_id)
    db.commit()
