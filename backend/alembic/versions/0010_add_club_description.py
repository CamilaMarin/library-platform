"""Add description column to clubs table

Revision ID: 0010
Revises: 0009
Create Date: 2025-07-26

Adds: clubs.description (nullable varchar(500))
Reference: M9 integration fixes — frontend expects club description field
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clubs", sa.Column("description", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("clubs", "description")
