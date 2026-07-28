"""SQLAlchemy models for the Community bounded context.

ORM representations — domain entities remain framework-free.
Reference: docs/architecture/database.md, ADR-0006
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ClubModel(Base):
    """ORM model for the clubs table.

    A club belongs to a single family group (ADR-0006).
    """

    __tablename__ = "clubs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    active_book_id = Column(UUID(as_uuid=True), nullable=True)
    discussion_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReadingTurnModel(Base):
    """ORM model for the reading_turns table."""

    __tablename__ = "reading_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    club_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), nullable=False)
    current_user_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CommentModel(Base):
    """ORM model for the turn_comments table."""

    __tablename__ = "turn_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turn_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    text = Column(Text, nullable=False)
    is_spoiler = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
