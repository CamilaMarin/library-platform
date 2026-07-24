"""SQLAlchemy models for the Library bounded context.

ORM representations — domain entities remain framework-free.
Reference: docs/architecture/database.md
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
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
