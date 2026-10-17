from .base import ServiceResult, not_implemented


class NeighborhoodService:
    def list_all(self) -> ServiceResult:
        return not_implemented("Neighborhood listing")
