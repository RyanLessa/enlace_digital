from typing import Any

from sqlalchemy.orm import Session

from enlace_digital.interface.models import Group
from enlace_digital.interface.repositories import SchoolNotFound, SchoolRepository
from enlace_digital.interface.repositories.school import (
    SchoolProfile,
    SchoolSearchResult,
)

from .base import ServiceResult


class SchoolService:
    def __init__(
        self,
        session: Session,
        repository: SchoolRepository | None = None,
    ) -> None:
        self.repository = repository or SchoolRepository(session)

    def search(
        self,
        *,
        neighborhood_id: int | None,
        groups: list[Group],
        query: str | None,
        limit: int,
        offset: int,
    ) -> ServiceResult:
        results = self.repository.search(
            neighborhood_id=neighborhood_id,
            groups=groups,
            query=query,
            limit=limit,
            offset=offset,
        )
        return ServiceResult(
            status_code=200,
            content={
                "items": [self._present_search_result(result) for result in results],
                "limit": limit,
                "offset": offset,
            },
        )

    def get_by_id(self, school_id: int) -> ServiceResult:
        try:
            profile = self.repository.get_profile(school_id)
        except SchoolNotFound:
            return ServiceResult(
                status_code=404,
                content={"detail": "School not found."},
            )
        return ServiceResult(
            status_code=200,
            content=self._present_profile(profile),
        )

    @staticmethod
    def _present_search_result(result: SchoolSearchResult) -> dict[str, Any]:
        return {
            "id": result.school.id,
            "name": result.school.name,
            "matched_groups": [group.value for group in result.matched_groups],
            "ranking_score": result.ranking_score,
        }

    @staticmethod
    def _present_profile(profile: SchoolProfile) -> dict[str, Any]:
        return {
            "id": profile.school.id,
            "name": profile.school.name,
            "neighborhood": {
                "id": profile.neighborhood.id,
                "name": profile.neighborhood.name,
                "municipality": profile.neighborhood.municipality,
            },
            "address": profile.school.address,
            "scores": [
                {
                    "group": score.group.value,
                    "average": score.average,
                    "review_count": score.review_count,
                }
                for score in profile.scores
            ],
        }
