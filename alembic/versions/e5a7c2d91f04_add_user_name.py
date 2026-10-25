"""add user name

Revision ID: e5a7c2d91f04
Revises: d6f81c20a9b3
Create Date: 2026-10-24 22:48:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5a7c2d91f04"
down_revision: Union[str, Sequence[str], None] = "d6f81c20a9b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=120), nullable=True))
    op.execute(sa.text("UPDATE users SET name = '' WHERE name IS NULL"))
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=120),
            nullable=False,
        )


def downgrade() -> None:
    op.drop_column("users", "name")
