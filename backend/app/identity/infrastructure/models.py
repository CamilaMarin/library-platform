"""SQLAlchemy models for the privacy foundation tables.

These are ORM representations — the domain entities remain framework-free.
Reference: docs/architecture/database.md
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class DataConsentModel(Base):
    """ORM model for the data_consents table."""

    __tablename__ = "data_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    policy_version = Column(String(50), nullable=False)
    purpose = Column(Text, nullable=False)


class DataProcessingRecordModel(Base):
    """ORM model for the data_processing_records table."""

    __tablename__ = "data_processing_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    data_type = Column(String(100), nullable=False)
    purpose = Column(Text, nullable=False)
    legal_basis = Column(String(200), nullable=False)
    collected_at = Column(DateTime, nullable=False, server_default=func.now())
    retention_expires_at = Column(DateTime, nullable=True)


class AuditLogModel(Base):
    """ORM model for the audit_logs table."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    affected_entity = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)


class RetentionPolicyModel(Base):
    """ORM model for the retention_policies table.

    Configurable at runtime — duration_days is never a code constant.
    Reference: ADR-0016
    """

    __tablename__ = "retention_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_type = Column(String(100), nullable=False, unique=True)
    duration_days = Column(Integer, nullable=False, default=365)
    description = Column(Text, nullable=False, default="")
    active = Column(Boolean, nullable=False, default=True)
