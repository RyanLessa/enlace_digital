from sqlalchemy import CheckConstraint, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enlace_digital.settings.get_db import Base

from .enums import Group, GroupCol, NOTA_MAX, NOTA_MIN


class SchoolGroupScore(Base):
    __tablename__ = "school_group_scores"

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id"), primary_key=True
    )
    group: Mapped[Group] = mapped_column(GroupCol, primary_key=True)
    has_adaptation: Mapped[bool] = mapped_column(
        default=False, server_default=text("0"), nullable=False
    )
    review_count: Mapped[int] = mapped_column(
        default=0, server_default=text("0"), nullable=False
    )
    score_sum: Mapped[int] = mapped_column(
        default=0, server_default=text("0"), nullable=False
    )

    school: Mapped["School"] = relationship(back_populates="scores")

    __table_args__ = (
        CheckConstraint(
            f"review_count >= 0 AND score_sum >= review_count * {NOTA_MIN} "
            f"AND score_sum <= review_count * {NOTA_MAX}",
            name="ck_wallet_bounds",
        ),
        Index("ix_wallet_group_school", "group", "school_id"),
    )
