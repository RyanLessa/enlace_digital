"""Add total review count to schools."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f6c4d8a1e3"
down_revision: Union[str, Sequence[str], None] = "6389ec0a8d08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "schools",
        sa.Column(
            "total_reviews",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE schools
        SET total_reviews = (
            SELECT COUNT(*)
            FROM reviews
            WHERE reviews.school_id = schools.id
        )
        """
    )


def downgrade() -> None:
    op.drop_column("schools", "total_reviews")
