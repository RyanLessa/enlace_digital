"""add review observation

Revision ID: d6f81c20a9b3
Revises: c41d938fac2b
Create Date: 2026-10-24 20:28:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d6f81c20a9b3"
down_revision: Union[str, Sequence[str], None] = "c41d938fac2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("observation", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "observation")
