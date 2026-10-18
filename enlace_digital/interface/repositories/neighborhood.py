from sqlalchemy import select
from sqlalchemy.orm import Session

from enlace_digital.interface.models import Neighborhood


class NeighborhoodRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Neighborhood]:
        statement = select(Neighborhood).order_by(
            Neighborhood.municipality, Neighborhood.name, Neighborhood.id
        )
        return list(self.session.scalars(statement))

    def get_by_id(self, neighborhood_id: int) -> Neighborhood | None:
        return self.session.get(Neighborhood, neighborhood_id)

    def get_by_name(
        self, name: str, municipality: str
    ) -> Neighborhood | None:
        statement = select(Neighborhood).where(
            Neighborhood.name == name,
            Neighborhood.municipality == municipality,
        )
        return self.session.scalar(statement)

    def get_or_create(self, name: str, municipality: str) -> Neighborhood:
        neighborhood = self.get_by_name(name, municipality)
        if neighborhood is not None:
            return neighborhood

        neighborhood = Neighborhood(name=name, municipality=municipality)
        self.session.add(neighborhood)
        self.session.flush()
        return neighborhood
