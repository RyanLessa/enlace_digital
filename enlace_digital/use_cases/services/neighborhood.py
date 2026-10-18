from sqlalchemy.orm import Session

from enlace_digital.interface.repositories import NeighborhoodRepository

from .base import ServiceResult


class NeighborhoodService:
    def __init__(
        self,
        session: Session,
        repository: NeighborhoodRepository | None = None,
    ) -> None:
        self.repository = repository or NeighborhoodRepository(session)

    def list_all(self) -> ServiceResult:
        neighborhoods = self.repository.list_all()
        return ServiceResult(
            status_code=200,
            content=[
                {
                    "id": neighborhood.id,
                    "name": neighborhood.name,
                    "municipality": neighborhood.municipality,
                    "slug": neighborhood.slug,
                }
                for neighborhood in neighborhoods
            ],
        )
