from enlace_digital.interface.models.enums import Group
from enlace_digital.use_cases.services import ReviewService, ServiceResult


class ReviewController:
    def __init__(self, service: ReviewService) -> None:
        self.service = service

    def list_for_school(
        self, *, school_id: int, limit: int, offset: int
    ) -> ServiceResult:
        return self.service.list_for_school(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )

    def create(
        self,
        *,
        school_id: int,
        scores: list[tuple[Group, int]],
        user_id: int | None = None,
        observation: str | None = None,
    ) -> ServiceResult:
        return self.service.create(
            school_id=school_id,
            scores=scores,
            user_id=user_id,
            observation=observation,
        )

    def update(
        self,
        *,
        school_id: int,
        scores: list[tuple[Group, int]],
        observation: str | None = None,
    ) -> ServiceResult:
        return self.service.update(
            school_id=school_id,
            scores=scores,
            observation=observation,
        )

    def delete(self, *, school_id: int) -> ServiceResult:
        return self.service.delete(school_id=school_id)
