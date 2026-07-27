"""SQLAlchemy models for the Circulation bounded context.

ORM representations — domain entities remain framework-free.
Reference: docs/architecture/database.md, ADR-0015
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class LoanModel(Base):
    """ORM model for the loans table."""

    __tablename__ = "loans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    copy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("copies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    borrower_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    loan_date = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    estimated_return_date = Column(DateTime(timezone=True), nullable=True)
    returned_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, server_default="active")
