from datetime import datetime

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enlace_digital.settings.get_db import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    name_normalized: Mapped[str] = mapped_column(String(200))
    neighborhood_id: Mapped[int] = mapped_column(
        ForeignKey("neighborhoods.id"), index=True
    )
    address: Mapped[str | None] = mapped_column(String(300))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    total_reviews: Mapped[int] = mapped_column(
        default=0, server_default=text("0"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, server_default=text("1"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    neighborhood: Mapped["Neighborhood"] = relationship(back_populates="schools")
    scores: Mapped[list["SchoolGroupScore"]] = relationship(
        back_populates="school"
    )
    reviews: Mapped[list["Review"]] = relationship(back_populates="school")

    __table_args__ = (
        UniqueConstraint("name_normalized", "neighborhood_id"),
    )
