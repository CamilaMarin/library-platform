"""SQLAlchemy models for the Library bounded context.

ORM representations — domain entities remain framework-free.
Reference: docs/architecture/database.md
"""

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.database import Base


class BookModel(Base):
    """ORM model for the books table."""

    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    author = Column(String(500), nullable=False)
    genres = Column(ARRAY(String(100)), nullable=False, server_default="{}")
    description = Column(Text, nullable=False, server_default="")
    pages = Column(Integer, nullable=True)
    isbn = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CopyModel(Base):
    """ORM model for the copies table."""

    __tablename__ = "copies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String(20), nullable=False)
    file_ref = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, server_default="available")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReadingStatusModel(Base):
    """ORM model for the reading_statuses table.

    Unique constraint on (user_id, book_id) enforces Property 1 from spec.
    ON DELETE CASCADE on both FKs handles ARCO cancellation automatically.
    """

    __tablename__ = "reading_statuses"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_reading_status_user_book"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(20), nullable=False)
    current_page = Column(Integer, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ReadingProgressModel(Base):
    """ORM model for the reading_progress table.

    Unique constraint on (user_id, copy_id) enforces Property 3 (idempotent upsert).
    ON DELETE CASCADE on both FKs handles ARCO cancellation automatically.
    Reference: .kiro/specs/reader/design.md
    """

    __tablename__ = "reading_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "copy_id", name="uq_reading_progress_user_copy"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    copy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("copies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position = Column(String(1000), nullable=False)
    file_format = Column(String(20), nullable=False)
    percentage = Column(Float, nullable=False, default=0.0)
    last_read_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
