"""Library tables (books, copies)

Revision ID: 0005
Revises: 0004
Create Date: 2025-07-22

Creates: books, copies
Reference: ADR-0015, library/tasks.md#1
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(500), nullable=False),
        sa.Column("genres", ARRAY(sa.String(100)), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("pages", sa.Integer, nullable=True),
        sa.Column("isbn", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "copies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("file_ref", sa.String(500), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="available",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_copies_user_id", "copies", ["user_id"])
    op.create_index("ix_copies_book_id", "copies", ["book_id"])


def downgrade() -> None:
    op.drop_index("ix_copies_book_id", table_name="copies")
    op.drop_index("ix_copies_user_id", table_name="copies")
    op.drop_table("copies")
    op.drop_table("books")
