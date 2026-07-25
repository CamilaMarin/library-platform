"""Reviews table

Revision ID: 0008
Revises: 0007
Create Date: 2025-07-24

Creates: reviews
Reference: ADR-0007, reviews/tasks.md#2
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=True),
        sa.Column("visibility", sa.String(20), nullable=False),
        sa.Column("shared_with_type", sa.String(20), nullable=True),
        sa.Column("shared_with_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])
    op.create_index("ix_reviews_book_id", "reviews", ["book_id"])


def downgrade() -> None:
    op.drop_index("ix_reviews_book_id", table_name="reviews")
    op.drop_index("ix_reviews_user_id", table_name="reviews")
    op.drop_table("reviews")
