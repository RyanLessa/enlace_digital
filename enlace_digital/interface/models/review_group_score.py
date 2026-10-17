from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enlace_digital.settings.get_db import Base

from .enums import Grupo, GrupoCol, NOTA_MAX, NOTA_MIN


class ReviewGroupScore(Base):
    __tablename__ = "review_group_scores"

    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id"), primary_key=True
    )
    group: Mapped[Grupo] = mapped_column(GrupoCol, primary_key=True)
    score: Mapped[int] = mapped_column(nullable=False)

    review: Mapped["Review"] = relationship(back_populates="scores")

    __table_args__ = (
        CheckConstraint(
            f"score BETWEEN {NOTA_MIN} AND {NOTA_MAX}",
            name="ck_score_range",
        ),
    )
