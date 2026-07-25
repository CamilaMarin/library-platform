"""SQLAlchemy models for Reading Selection.

Reference: docs/architecture/database.md
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID

from app.database import Base


class DrawModel(Base):
    """ORM model for the draws table."""

    __tablename__ = "draws"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("family_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filters = Column(JSON, nullable=False, server_default="{}")
    participants = Column(ARRAY(String), nullable=False)
    result_book_id = Column(UUID(as_uuid=True), nullable=True)
    result_source_user_id = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TurnHistoryModel(Base):
    """ORM model for the turn_histories table."""

    __tablename__ = "turn_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("family_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    last_pick_date = Column(DateTime(timezone=True), nullable=True)
