from datetime import datetime

from sqlalchemy import ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enlace_digital.settings.get_db import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    is_hidden: Mapped[bool] = mapped_column(
        default=False, server_default=text("0"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    school: Mapped["School"] = relationship(back_populates="reviews")
    user: Mapped["User | None"] = relationship(back_populates="reviews")
    scores: Mapped[list["ReviewGroupScore"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "uq_review_user_school",
            "user_id",
            "school_id",
            unique=True,
            sqlite_where=text("user_id IS NOT NULL"),
        ),
        Index("ix_reviews_school_created", "school_id", "created_at"),
    )
