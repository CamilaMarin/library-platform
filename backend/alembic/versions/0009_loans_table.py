"""Loans table

Revision ID: 0009
Revises: 0008
Create Date: 2025-07-25

Creates: loans
Reference: ADR-0015, loans/tasks.md#2
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "loans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "copy_id",
            UUID(as_uuid=True),
            sa.ForeignKey("copies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "borrower_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "loan_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("estimated_return_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="active"
        ),
    )
    op.create_index("ix_loans_copy_id", "loans", ["copy_id"])
    op.create_index("ix_loans_borrower_user_id", "loans", ["borrower_user_id"])


def downgrade() -> None:
    op.drop_index("ix_loans_borrower_user_id", table_name="loans")
    op.drop_index("ix_loans_copy_id", table_name="loans")
    op.drop_table("loans")
