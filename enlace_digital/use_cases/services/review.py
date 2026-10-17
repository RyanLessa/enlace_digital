from enlace_digital.interface.models.enums import Group

from .base import ServiceResult, not_implemented


class ReviewService:
    def list_for_school(
        self, *, school_id: int, limit: int, offset: int
    ) -> ServiceResult:
        del school_id, limit, offset
        return not_implemented("Review listing")

    def create(
        self, *, school_id: int, scores: list[tuple[Group, int]]
    ) -> ServiceResult:
        del school_id, scores
        return not_implemented("Review creation")

    def update(
        self, *, school_id: int, scores: list[tuple[Group, int]]
    ) -> ServiceResult:
        del school_id, scores
        return not_implemented("Review updates")

    def delete(self, *, school_id: int) -> ServiceResult:
        del school_id
        return not_implemented("Review deletion")
