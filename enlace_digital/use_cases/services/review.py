from typing import Any

from sqlalchemy.orm import Session

from enlace_digital.interface.models import Group, Review
from enlace_digital.interface.repositories import (
    PublicReview,
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
        try:
            self.schools.get_profile(school_id)
        except SchoolNotFound:
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
            self.schools.get_profile(school_id)
        except SchoolNotFound:
            return ServiceResult(404, {"detail": "Escola não encontrada."})

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
        groups = [group for group, _ in scores]

        VALIDATION_RULES = (
            (
                lambda groups, scores: any(not isinstance(g, Group) for g in groups),
                "Unknown accessibility group.",
            ),
            (
                lambda groups, scores: len(groups) != len(set(groups)),
                "Groups must be unique.",
            ),
            (
                lambda groups, scores: any(
                    type(score) is not int or not 1 <= score <= 5 for _, score in scores
                ),
                "Each group score must be an integer from 1 to 5.",
            ),
        )

        for is_invalid, message in VALIDATION_RULES:
            if is_invalid(groups, scores):
                return ServiceResult(422, {"detail": message})

    @staticmethod
    def _present_review(review: Review | PublicReview) -> dict[str, Any]:
        from_registered_user = (
            review.from_registered_user
            if isinstance(review, PublicReview)
            else review.user_id is not None
        )
        return {
            "id": review.id,
            "school_id": review.school_id,
            "created_at": review.created_at.isoformat(),
            "from_registered_user": from_registered_user,
            "observation": review.observation,
            "scores": [
                {"group": score.group.value, "score": score.score}
                for score in sorted(review.scores, key=lambda item: item.group.value)
            ],
        }
