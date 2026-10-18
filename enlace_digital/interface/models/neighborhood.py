from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enlace_digital.settings.get_db import Base


class Neighborhood(Base):
    __tablename__ = "neighborhoods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    municipality: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(255))

    schools: Mapped[list["School"]] = relationship(back_populates="neighborhood")

    __table_args__ = (
        UniqueConstraint("name", "municipality"),
        UniqueConstraint("slug", name="uq_neighborhoods_slug"),
    )
