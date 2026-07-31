"""Create reading_progress table

Revision ID: 0013
Revises: 0012
Create Date: 2025-07-29

Creates: reading_progress table for tracking user reading positions.
Reference: .kiro/specs/reader/design.md — Property 2, 3
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reading_progress",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "copy_id",
            UUID(as_uuid=True),
            sa.ForeignKey("copies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("position", sa.String(1000), nullable=False),
        sa.Column("file_format", sa.String(20), nullable=False),
        sa.Column("percentage", sa.Float, nullable=False, server_default="0.0"),
        sa.Column(
            "last_read_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "copy_id", name="uq_reading_progress_user_copy"),
    )


def downgrade() -> None:
    op.drop_table("reading_progress")
