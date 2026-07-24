"""SQLAlchemy models for the privacy foundation tables.

These are ORM representations — the domain entities remain framework-free.
Reference: docs/architecture/database.md
"""

import uuid

import sqlalchemy as sa
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID

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


class UserModel(Base):
    """ORM model for the users table."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    email = Column(String(320), nullable=False, unique=True, index=True)
    password_hash = Column(String(200), nullable=False)
    privacy_settings = Column(JSON, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RefreshTokenModel(Base):
    """ORM model for the refresh_tokens table."""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class FamilyGroupModel(Base):
    """ORM model for the family_groups table."""

    __tablename__ = "family_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class GroupMembershipModel(Base):
    """ORM model for the group_memberships table."""

    __tablename__ = "group_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_memberships_group_user"),
    )
