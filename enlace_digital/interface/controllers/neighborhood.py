from enlace_digital.use_cases.services import NeighborhoodService, ServiceResult


class NeighborhoodController:
    def __init__(self, service: NeighborhoodService) -> None:
        self.service = service

    def list_all(self) -> ServiceResult:
        return self.service.list_all()
