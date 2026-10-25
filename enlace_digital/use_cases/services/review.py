from typing import Any

from sqlalchemy.orm import Session

from enlace_digital.interface.models import Group, Review
from enlace_digital.interface.repositories import (
    ReviewRepository,
    SchoolNotFound,
    SchoolRepository,
)

from .base import ServiceResult


class ReviewService:
    def __init__(
        self,
        session: Session,
        review_repository: ReviewRepository | None = None,
        school_repository: SchoolRepository | None = None,
    ) -> None:
        self.session = session
        self.reviews = review_repository or ReviewRepository(session)
        self.schools = school_repository or SchoolRepository(session)

    def list_for_school(
        self,
        *,
        school_id: int,
        limit: int,
        offset: int,
    ) -> ServiceResult:
        if not self.schools.exists_active(school_id):
            return ServiceResult(404, {"detail": "Escola não encontrada."})

        reviews = self.reviews.list_public(
            school_id,
            limit=limit,
            offset=offset,
        )
        return ServiceResult(
            200,
            {
                "items": [self._present_review(review) for review in reviews],
                "limit": limit,
                "offset": offset,
            },
        )

    def create(
        self,
        *,
        school_id: int,
        scores: list[tuple[Group, int]],
        user_id: int | None = None,
        observation: str | None = None,
    ) -> ServiceResult:
        invalid_scores = self._validate_scores(scores)
        if invalid_scores is not None:
            return invalid_scores

        try:
            review = self.reviews.create(
                school_id=school_id,
                scores=scores,
                user_id=user_id,
                observation=observation,
            )
            self.session.commit()
        except SchoolNotFound:
            self.session.rollback()
            return ServiceResult(404, {"detail": "Escola não encontrada."})
        except Exception:
            self.session.rollback()
            raise

        return ServiceResult(201, self._present_review(review))

    def update(
        self,
        *,
        school_id: int,
        scores: list[tuple[Group, int]],
        observation: str | None = None,
    ) -> ServiceResult:
        del school_id, scores, observation
        return ServiceResult(
            501,
            {"detail": "Review updates require authentication support."},
        )

    def delete(self, *, school_id: int) -> ServiceResult:
        del school_id
        return ServiceResult(
            501,
            {"detail": "Review deletion requires authentication support."},
        )

    @staticmethod
    def _validate_scores(
        scores: list[tuple[Group, int]],
    ) -> ServiceResult | None:
        if not 1 <= len(scores) <= 5:
            return ServiceResult(
                422,
                {"detail": "Provide scores for between one and five groups."},
            )
        seen_groups: set[Group] = set()
        for group, score in scores:
            if not isinstance(group, Group):
                return ServiceResult(422, {"detail": "Unknown accessibility group."})
            if group in seen_groups:
                return ServiceResult(422, {"detail": "Groups must be unique."})
            if type(score) is not int or not 1 <= score <= 5:
                return ServiceResult(
                    422,
                    {"detail": "Each group score must be an integer from 1 to 5."},
                )
            seen_groups.add(group)

    @staticmethod
    def _present_review(review: Review) -> dict[str, Any]:
        return {
            "id": review.id,
            "school_id": review.school_id,
            "created_at": review.created_at.isoformat(),
            "from_registered_user": review.user_id is not None,
            "user_name": review.user.name if review.user is not None else None,
            "observation": review.observation,
            "scores": [
                {"group": score.group.value, "score": score.score}
                for score in sorted(review.scores, key=lambda item: item.group.value)
            ],
        }
