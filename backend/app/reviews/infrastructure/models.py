"""SQLAlchemy models for the Reviews bounded context.

ORM representations — domain entities remain framework-free.
Reference: docs/architecture/database.md, ADR-0007
"""

import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ReviewModel(Base):
    """ORM model for the reviews table."""

    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    visibility = Column(String(20), nullable=False)
    shared_with_type = Column(String(20), nullable=True)
    shared_with_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
