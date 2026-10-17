from enlace_digital.interface.models.enums import Group
from enlace_digital.use_cases.services import SchoolService, ServiceResult


class SchoolController:
    def __init__(self, service: SchoolService | None = None) -> None:
        self.service = service or SchoolService()

    def search(
        self,
        *,
        neighborhood_id: int | None,
        groups: list[Group],
        query: str | None,
        limit: int,
        offset: int,
    ) -> ServiceResult:
        return self.service.search(
            neighborhood_id=neighborhood_id,
            groups=groups,
            query=query,
            limit=limit,
            offset=offset,
        )

    def get_by_id(self, school_id: int) -> ServiceResult:
        return self.service.get_by_id(school_id)
