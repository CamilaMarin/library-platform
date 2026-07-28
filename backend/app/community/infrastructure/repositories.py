"""Repository implementations for the Community bounded context.

Implements protocols from application/protocols.py.
Reference: ADR-0017, ADR-0006
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.community.domain.entities import Club, Comment, ReadingTurn
from app.community.infrastructure.models import ClubModel, CommentModel, ReadingTurnModel


class SqlClubRepository:
    """SQLAlchemy implementation of ClubRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, club: Club) -> Club:
        model = ClubModel(
            id=club.id,
            group_id=club.group_id,
            name=club.name,
            description=club.description,
            active_book_id=club.active_book_id,
            discussion_date=club.discussion_date,
            created_at=club.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return club

    def find_by_id(self, club_id: UUID) -> Club | None:
        model = self._session.get(ClubModel, club_id)
        if not model:
            return None
        return self._to_domain(model)

    def find_by_group_ids(self, group_ids: list[UUID]) -> list[Club]:
        """Find all clubs belonging to the given groups."""
        if not group_ids:
            return []
        models = (
            self._session.query(ClubModel)
            .filter(ClubModel.group_id.in_(group_ids))
            .order_by(ClubModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def update(self, club: Club) -> Club:
        model = self._session.get(ClubModel, club.id)
        if not model:
            raise ValueError(f"Club {club.id} not found")
        model.name = club.name
        model.description = club.description
        model.active_book_id = club.active_book_id
        model.discussion_date = club.discussion_date
        self._session.flush()
        return club

    def _to_domain(self, model: ClubModel) -> Club:
        return Club(
            id=model.id,
            group_id=model.group_id,
            name=model.name,
            description=model.description,
            active_book_id=model.active_book_id,
            discussion_date=model.discussion_date,
            created_at=model.created_at,
        )


class SqlReadingTurnRepository:
    """SQLAlchemy implementation of ReadingTurnRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, turn: ReadingTurn) -> ReadingTurn:
        model = ReadingTurnModel(
            id=turn.id,
            club_id=turn.club_id,
            book_id=turn.book_id,
            current_user_id=turn.current_user_id,
            created_at=turn.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return turn

    def find_by_club(self, club_id: UUID) -> list[ReadingTurn]:
        models = (
            self._session.query(ReadingTurnModel)
            .filter(ReadingTurnModel.club_id == club_id)
            .order_by(ReadingTurnModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def find_active_by_club(self, club_id: UUID) -> ReadingTurn | None:
        """Find the most recent reading turn for a club (the active one)."""
        model = (
            self._session.query(ReadingTurnModel)
            .filter(ReadingTurnModel.club_id == club_id)
            .order_by(ReadingTurnModel.created_at.desc())
            .first()
        )
        if not model:
            return None
        return self._to_domain(model)

    def _to_domain(self, model: ReadingTurnModel) -> ReadingTurn:
        return ReadingTurn(
            id=model.id,
            club_id=model.club_id,
            book_id=model.book_id,
            current_user_id=model.current_user_id,
            created_at=model.created_at,
        )


class SqlCommentRepository:
    """SQLAlchemy implementation of CommentRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, comment: Comment) -> Comment:
        model = CommentModel(
            id=comment.id,
            turn_id=comment.turn_id,
            user_id=comment.user_id,
            text=comment.text,
            is_spoiler=comment.is_spoiler,
            created_at=comment.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return comment

    def find_by_turn(self, turn_id: UUID) -> list[Comment]:
        models = (
            self._session.query(CommentModel)
            .filter(CommentModel.turn_id == turn_id)
            .order_by(CommentModel.created_at.asc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: CommentModel) -> Comment:
        return Comment(
            id=model.id,
            turn_id=model.turn_id,
            user_id=model.user_id,
            text=model.text,
            is_spoiler=model.is_spoiler,
            created_at=model.created_at,
        )
