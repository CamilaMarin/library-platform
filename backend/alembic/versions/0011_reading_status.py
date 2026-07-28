"""Add reading_statuses table

Revision ID: 0011
Revises: 0010
Create Date: 2025-07-28

Adds: reading_statuses table with (user_id, book_id) unique constraint.
Supports upsert of personal reading status per book (want_to_read | reading | read | dnf).
ON DELETE CASCADE on both FKs covers ARCO cancellation automatically.
Reference: .kiro/specs/reading-status/design.md
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reading_statuses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "book_id", name="uq_reading_status_user_book"),
    )
    op.create_index("ix_reading_statuses_user_id", "reading_statuses", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_reading_statuses_user_id", table_name="reading_statuses")
    op.drop_table("reading_statuses")
