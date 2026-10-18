"""add unique neighborhood slugs

Revision ID: c41d938fac2b
Revises: a5873d266db7
Create Date: 2026-10-18 00:00:00.000000
"""
import re
import unicodedata
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c41d938fac2b"
down_revision: Union[str, Sequence[str], None] = "a5873d266db7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slugify(name: str, municipality: str) -> str:
    value = unicodedata.normalize(
        "NFKD",
        f"{name}-{municipality}".casefold(),
    )
    unaccented = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "-", unaccented).strip("-")


def upgrade() -> None:
    op.add_column(
        "neighborhoods",
        sa.Column("slug", sa.String(length=255), nullable=True),
    )

    connection = op.get_bind()
    neighborhoods = connection.execute(
        sa.text("SELECT id, name, municipality FROM neighborhoods ORDER BY id")
    ).mappings()
    used_slugs: set[str] = set()
    for neighborhood in neighborhoods:
        base_slug = _slugify(
            neighborhood["name"],
            neighborhood["municipality"],
        )
        slug = base_slug
        if slug in used_slugs:
            slug = f"{base_slug}-{neighborhood['id']}"
        suffix = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{neighborhood['id']}-{suffix}"
            suffix += 1
        used_slugs.add(slug)
        connection.execute(
            sa.text("UPDATE neighborhoods SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": neighborhood["id"]},
        )

    with op.batch_alter_table("neighborhoods") as batch_op:
        batch_op.alter_column(
            "slug",
            existing_type=sa.String(length=255),
            nullable=False,
        )
        batch_op.create_unique_constraint("uq_neighborhoods_slug", ["slug"])


def downgrade() -> None:
    with op.batch_alter_table("neighborhoods") as batch_op:
        batch_op.drop_constraint("uq_neighborhoods_slug", type_="unique")
        batch_op.drop_column("slug")
