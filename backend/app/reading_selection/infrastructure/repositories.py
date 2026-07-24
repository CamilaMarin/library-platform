"""Repository implementations for Reading Selection.

Reference: ADR-0017 (infrastructure implements abstractions)
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.library.domain.entities import Book, Copy, CopyStatus, CopyType
from app.library.infrastructure.models import BookModel, CopyModel
from app.reading_selection.domain.entities import Draw, TurnHistory
from app.reading_selection.infrastructure.models import DrawModel, TurnHistoryModel


class SqlDrawRepository:
    """SQLAlchemy implementation of DrawRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, draw: Draw) -> Draw:
        model = DrawModel(
            id=draw.id,
            group_id=draw.group_id,
            filters=draw.filters,
            participants=[str(p) for p in draw.participants],
            result_book_id=draw.result_book_id,
            result_source_user_id=draw.result_source_user_id,
            timestamp=draw.timestamp,
        )
        self._session.add(model)
        self._session.flush()
        return draw

    def find_by_group(self, group_id: UUID) -> list[Draw]:
        models = (
            self._session.query(DrawModel)
            .filter(DrawModel.group_id == group_id)
            .order_by(DrawModel.timestamp.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def find_result_book_ids_by_group(self, group_id: UUID) -> list[UUID]:
        """Return all previously drawn book IDs for a group."""
        results = (
            self._session.query(DrawModel.result_book_id)
            .filter(DrawModel.group_id == group_id)
            .filter(DrawModel.result_book_id.isnot(None))
            .all()
        )
        return [r[0] for r in results]

    def _to_domain(self, model: DrawModel) -> Draw:
        return Draw(
            id=model.id,
            group_id=model.group_id,
            filters=model.filters or {},
            participants=(
                [UUID(p) for p in model.participants] if model.participants else []
            ),
            result_book_id=model.result_book_id,
            result_source_user_id=model.result_source_user_id,
            timestamp=model.timestamp,
        )


class SqlTurnHistoryRepository:
    """SQLAlchemy implementation of TurnHistoryRepository."""

    def __init__(self, session: Session):
        self._session = session

    def find_by_group(self, group_id: UUID) -> list[TurnHistory]:
        models = (
            self._session.query(TurnHistoryModel)
            .filter(TurnHistoryModel.group_id == group_id)
            .all()
        )
        return [
            TurnHistory(
                id=m.id,
                group_id=m.group_id,
                user_id=m.user_id,
                last_pick_date=m.last_pick_date,
            )
            for m in models
        ]

    def save_or_update(self, turn: TurnHistory) -> TurnHistory:
        existing = self._session.get(TurnHistoryModel, turn.id)
        if existing:
            existing.last_pick_date = turn.last_pick_date
        else:
            model = TurnHistoryModel(
                id=turn.id,
                group_id=turn.group_id,
                user_id=turn.user_id,
                last_pick_date=turn.last_pick_date,
            )
            self._session.add(model)
        self._session.flush()
        return turn


class SqlCopyQueryService:
    """Read-only query into Library for copy availability.

    Never returns file_ref (Property 3 / ADR-0009).
    """

    def __init__(self, session: Session):
        self._session = session

    def find_copies_for_books(
        self, book_ids: list[UUID], participant_ids: list[UUID]
    ) -> dict[UUID, list[Copy]]:
        """Find copies grouped by book_id for participants."""
        if not book_ids or not participant_ids:
            return {}

        models = (
            self._session.query(CopyModel)
            .filter(CopyModel.book_id.in_(book_ids))
            .filter(CopyModel.user_id.in_(participant_ids))
            .all()
        )

        result: dict[UUID, list[Copy]] = {}
        for m in models:
            copy = Copy(
                id=m.id,
                user_id=m.user_id,
                book_id=m.book_id,
                type=CopyType(m.type),
                file_ref=None,  # NEVER expose file_ref (ADR-0009)
                status=CopyStatus(m.status),
                created_at=m.created_at,
            )
            result.setdefault(m.book_id, []).append(copy)

        return result


class SqlBookQueryService:
    """Read-only query for books accessible to group members."""

    def __init__(self, session: Session):
        self._session = session

    def find_books_by_group_members(
        self,
        member_ids: list[UUID],
        genre: str | None = None,
        max_pages: int | None = None,
    ) -> list[Book]:
        """Find books with copies owned by members, optionally filtered."""
        if not member_ids:
            return []

        query = (
            self._session.query(BookModel)
            .join(CopyModel, CopyModel.book_id == BookModel.id)
            .filter(CopyModel.user_id.in_(member_ids))
        )

        if genre:
            query = query.filter(BookModel.genres.any(genre))

        if max_pages:
            query = query.filter(BookModel.pages <= max_pages)

        models = query.distinct().all()

        return [
            Book(
                id=m.id,
                title=m.title,
                author=m.author,
                genres=list(m.genres) if m.genres else [],
                description=m.description or "",
                pages=m.pages,
                isbn=m.isbn,
                created_at=m.created_at,
            )
            for m in models
        ]
