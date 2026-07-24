"""Privacy foundation tables

Revision ID: 0002
Revises: 0001
Create Date: 2025-07-21

Creates: data_consents, data_processing_records, audit_logs, retention_policies
Reference: ADR-0003, ADR-0016, privacy/tasks.md#1
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_consents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
    )

    op.create_table(
        "data_processing_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("data_type", sa.String(100), nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("legal_basis", sa.String(200), nullable=False),
        sa.Column("collected_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("retention_expires_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("affected_entity", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    op.create_table(
        "retention_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("data_type", sa.String(100), nullable=False, unique=True),
        sa.Column("duration_days", sa.Integer, nullable=False, server_default="365"),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_table("retention_policies")
    op.drop_index("ix_audit_logs_timestamp", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("data_processing_records")
    op.drop_table("data_consents")
