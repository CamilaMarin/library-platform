"""Repository implementations for the Library bounded context.

Implements protocols from application/protocols.py.
Reference: ADR-0017
"""

from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.library.domain.entities import Book, Copy, CopyStatus, CopyType
from app.library.infrastructure.models import BookModel, CopyModel


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

    def find_by_user_copies(self, user_id: UUID) -> list[Book]:
        """Find all books that the user owns a copy of."""
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
