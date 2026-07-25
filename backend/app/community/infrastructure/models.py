"""SQLAlchemy models for the Community bounded context.

ORM representations — domain entities remain framework-free.
Reference: docs/architecture/database.md, ADR-0006
"""

import uuid

from sqlalchemy import Column, DateTime, String, func
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
    active_book_id = Column(UUID(as_uuid=True), nullable=True)
    discussion_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
