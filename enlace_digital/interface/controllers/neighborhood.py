from enlace_digital.use_cases.services import NeighborhoodService, ServiceResult


class NeighborhoodController:
    def __init__(self, service: NeighborhoodService | None = None) -> None:
        self.service = service or NeighborhoodService()

    def list_all(self) -> ServiceResult:
        return self.service.list_all()
