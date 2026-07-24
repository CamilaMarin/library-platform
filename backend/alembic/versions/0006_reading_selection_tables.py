"""Reading Selection tables (draws, turn_histories)

Revision ID: 0006
Revises: 0005
Create Date: 2025-07-22

Creates: draws, turn_histories
Reference: ADR-0008, ADR-0013, reading-selection/tasks.md#1, #5
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "draws",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "group_id",
            UUID(as_uuid=True),
            sa.ForeignKey("family_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filters", JSON, nullable=False, server_default="{}"),
        sa.Column("participants", ARRAY(UUID(as_uuid=True)), nullable=False),
        sa.Column("result_book_id", UUID(as_uuid=True), nullable=True),
        sa.Column("result_source_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_draws_group_id", "draws", ["group_id"])

    op.create_table(
        "turn_histories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "group_id",
            UUID(as_uuid=True),
            sa.ForeignKey("family_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("last_pick_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_turn_histories_group_id", "turn_histories", ["group_id"])


def downgrade() -> None:
    op.drop_index("ix_turn_histories_group_id", table_name="turn_histories")
    op.drop_table("turn_histories")
    op.drop_index("ix_draws_group_id", table_name="draws")
    op.drop_table("draws")
