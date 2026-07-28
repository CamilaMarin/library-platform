"""Repository implementations for the Library bounded context.

Implements protocols from application/protocols.py.
Reference: ADR-0017
"""

from uuid import UUID

from sqlalchemy import or_, union
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.library.domain.entities import (
    Book,
    Copy,
    CopyStatus,
    CopyType,
    ReadingStatus,
    ReadingStatusValue,
)
from app.library.infrastructure.models import BookModel, CopyModel, ReadingStatusModel


class SqlBookRepository:
    """SQLAlchemy implementation of BookRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, book: Book) -> Book:
        model = BookModel(
            id=book.id,
            title=book.title,
            author=book.author,
            genres=book.genres,
            description=book.description,
            pages=book.pages,
            isbn=book.isbn,
            created_at=book.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return book

    def find_by_id(self, book_id: UUID) -> Book | None:
        model = self._session.get(BookModel, book_id)
        if not model:
            return None
        return self._to_domain(model)

    def find_by_user_books(self, user_id: UUID) -> list[Book]:
        """Find all books the user has access to: books with copies OR books
        the user has tagged with a reading status (e.g. want_to_read without
        owning a copy yet).

        This is the primary query for the library page.
        """
        combined = union(
            self._session.query(CopyModel.book_id).filter(
                CopyModel.user_id == user_id
            ),
            self._session.query(ReadingStatusModel.book_id).filter(
                ReadingStatusModel.user_id == user_id
            ),
        ).subquery()

        models = (
            self._session.query(BookModel)
            .filter(BookModel.id.in_(self._session.query(combined)))
            .order_by(BookModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def find_by_user_copies(self, user_id: UUID) -> list[Book]:
        """Find all books that the user owns a copy of.
        Kept for backward compatibility (draw availability checks).
        """
        models = (
            self._session.query(BookModel)
            .join(CopyModel, CopyModel.book_id == BookModel.id)
            .filter(CopyModel.user_id == user_id)
            .distinct()
            .all()
        )
        return [self._to_domain(m) for m in models]

    def find_by_group_members(self, member_ids: list[UUID]) -> list[Book]:
        """Find all books with copies owned by any group member."""
        if not member_ids:
            return []
        models = (
            self._session.query(BookModel)
            .join(CopyModel, CopyModel.book_id == BookModel.id)
            .filter(CopyModel.user_id.in_(member_ids))
            .distinct()
            .all()
        )
        return [self._to_domain(m) for m in models]

    def search(
        self, query: str, user_id: UUID, group_member_ids: list[UUID] | None = None
    ) -> list[Book]:
        """Search books by title/author/isbn within user's and group's library."""
        like_query = f"%{query}%"
        owner_ids = [user_id]
        if group_member_ids:
            owner_ids.extend(group_member_ids)

        models = (
            self._session.query(BookModel)
            .join(CopyModel, CopyModel.book_id == BookModel.id)
            .filter(CopyModel.user_id.in_(owner_ids))
            .filter(
                or_(
                    BookModel.title.ilike(like_query),
                    BookModel.author.ilike(like_query),
                    BookModel.isbn.ilike(like_query),
                )
            )
            .distinct()
            .all()
        )
        return [self._to_domain(m) for m in models]

    def update(self, book: Book) -> Book:
        model = self._session.get(BookModel, book.id)
        if model:
            model.title = book.title
            model.author = book.author
            model.genres = book.genres
            model.description = book.description
            model.pages = book.pages
            model.isbn = book.isbn
            self._session.flush()
        return book

    def delete(self, book_id: UUID) -> None:
        model = self._session.get(BookModel, book_id)
        if model:
            self._session.delete(model)
            self._session.flush()

    def has_copies(self, book_id: UUID) -> bool:
        count = (
            self._session.query(CopyModel)
            .filter(CopyModel.book_id == book_id)
            .count()
        )
        return count > 0

    def _to_domain(self, model: BookModel) -> Book:
        return Book(
            id=model.id,
            title=model.title,
            author=model.author,
            genres=list(model.genres) if model.genres else [],
            description=model.description or "",
            pages=model.pages,
            isbn=model.isbn,
            created_at=model.created_at,
        )


class SqlCopyRepository:
    """SQLAlchemy implementation of CopyRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, copy: Copy) -> Copy:
        model = CopyModel(
            id=copy.id,
            user_id=copy.user_id,
            book_id=copy.book_id,
            type=copy.type.value,
            file_ref=copy.file_ref,
            status=copy.status.value,
            created_at=copy.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return copy

    def find_by_id(self, copy_id: UUID) -> Copy | None:
        model = self._session.get(CopyModel, copy_id)
        if not model:
            return None
        return self._to_domain(model)

    def find_by_user(self, user_id: UUID) -> list[Copy]:
        models = (
            self._session.query(CopyModel)
            .filter(CopyModel.user_id == user_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def find_by_book(self, book_id: UUID) -> list[Copy]:
        models = (
            self._session.query(CopyModel)
            .filter(CopyModel.book_id == book_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def update(self, copy: Copy) -> Copy:
        model = self._session.get(CopyModel, copy.id)
        if model:
            model.type = copy.type.value
            model.file_ref = copy.file_ref
            model.status = copy.status.value
            self._session.flush()
        return copy

    def delete(self, copy_id: UUID) -> None:
        model = self._session.get(CopyModel, copy_id)
        if model:
            self._session.delete(model)
            self._session.flush()

    def _to_domain(self, model: CopyModel) -> Copy:
        return Copy(
            id=model.id,
            user_id=model.user_id,
            book_id=model.book_id,
            type=CopyType(model.type),
            file_ref=model.file_ref,
            status=CopyStatus(model.status),
            created_at=model.created_at,
        )


class SqlReadingStatusRepository:
    """SQLAlchemy implementation of ReadingStatusRepository.

    Uses PostgreSQL INSERT ... ON CONFLICT DO UPDATE (upsert) to enforce
    the UNIQUE(user_id, book_id) constraint cleanly (Property 1).
    """

    def __init__(self, session: Session):
        self._session = session

    def upsert(self, reading_status: ReadingStatus) -> ReadingStatus:
        """Insert or update the status for a (user_id, book_id) pair."""
        stmt = (
            pg_insert(ReadingStatusModel)
            .values(
                id=reading_status.id,
                user_id=reading_status.user_id,
                book_id=reading_status.book_id,
                status=reading_status.status.value,
                current_page=reading_status.current_page,
                updated_at=reading_status.updated_at,
            )
            .on_conflict_do_update(
                constraint="uq_reading_status_user_book",
                set_={
                    "status": reading_status.status.value,
                    "current_page": reading_status.current_page,
                    "updated_at": reading_status.updated_at,
                },
            )
        )
        self._session.execute(stmt)
        self._session.flush()
        return reading_status

    def find_by_user(self, user_id: UUID) -> list[ReadingStatus]:
        """Return all reading statuses for a user (Property 3 — user-scoped)."""
        models = (
            self._session.query(ReadingStatusModel)
            .filter(ReadingStatusModel.user_id == user_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def find_by_user_and_book(self, user_id: UUID, book_id: UUID) -> ReadingStatus | None:
        model = (
            self._session.query(ReadingStatusModel)
            .filter(
                ReadingStatusModel.user_id == user_id,
                ReadingStatusModel.book_id == book_id,
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def delete(self, user_id: UUID, book_id: UUID) -> None:
        """Remove status. Idempotent — no error if not found (Req 1.4)."""
        self._session.query(ReadingStatusModel).filter(
            ReadingStatusModel.user_id == user_id,
            ReadingStatusModel.book_id == book_id,
        ).delete(synchronize_session=False)
        self._session.flush()

    def _to_domain(self, model: ReadingStatusModel) -> ReadingStatus:
        return ReadingStatus(
            id=model.id,
            user_id=model.user_id,
            book_id=model.book_id,
            status=ReadingStatusValue(model.status),
            current_page=model.current_page,
            updated_at=model.updated_at,
        )
