"""Community tables (clubs, reading_turns, turn_comments)

Revision ID: 0007
Revises: 0006
Create Date: 2025-07-24

Creates: clubs, reading_turns, turn_comments
Reference: ADR-0006, clubs/tasks.md#1
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clubs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "group_id",
            UUID(as_uuid=True),
            sa.ForeignKey("family_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("active_book_id", UUID(as_uuid=True), nullable=True),
        sa.Column("discussion_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_clubs_group_id", "clubs", ["group_id"])

    op.create_table(
        "reading_turns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "club_id",
            UUID(as_uuid=True),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("book_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "current_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "turn_comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "turn_id",
            UUID(as_uuid=True),
            sa.ForeignKey("reading_turns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("is_spoiler", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("turn_comments")
    op.drop_table("reading_turns")
    op.drop_index("ix_clubs_group_id", table_name="clubs")
    op.drop_table("clubs")
