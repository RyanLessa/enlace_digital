from enlace_digital.interface.models.enums import Group

from .base import ServiceResult, not_implemented


class SchoolService:
    def search(
        self,
        *,
        neighborhood_id: int | None,
        groups: list[Group],
        query: str | None,
        limit: int,
        offset: int,
    ) -> ServiceResult:
        del neighborhood_id, groups, query, limit, offset
        return not_implemented("School search")

    def get_by_id(self, school_id: int) -> ServiceResult:
        del school_id
        return not_implemented("School details")
