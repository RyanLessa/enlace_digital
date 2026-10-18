import re
import unicodedata

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

    def get_by_slug(self, slug: str) -> Neighborhood | None:
        statement = select(Neighborhood).where(Neighborhood.slug == slug)
        return self.session.scalar(statement)

    def get_or_create(self, name: str, municipality: str) -> Neighborhood:
        name = name.strip()
        municipality = municipality.strip()
        if not name or not municipality:
            raise ValueError("Neighborhood name and municipality are required.")

        neighborhood = self.get_by_name(name, municipality)
        if neighborhood is not None:
            return neighborhood

        slug = self._build_slug(name, municipality)
        neighborhood = self.get_by_slug(slug)
        if neighborhood is not None:
            return neighborhood

        neighborhood = Neighborhood(
            name=name,
            municipality=municipality,
            slug=slug,
        )
        self.session.add(neighborhood)
        self.session.flush()
        return neighborhood

    @staticmethod
    def _build_slug(name: str, municipality: str) -> str:
        value = f"{name}-{municipality}".casefold()
        decomposed = unicodedata.normalize("NFKD", value)
        ascii_value = "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        )
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
        if not slug:
            raise ValueError("Neighborhood name and municipality must form a slug.")
        return slug
