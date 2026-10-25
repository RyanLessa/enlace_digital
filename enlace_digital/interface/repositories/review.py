from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from enlace_digital.interface.models import (
    Group,
    Review,
    ReviewGroupScore,
    School,
)

from .exceptions import ReviewNotFound, SchoolNotFound
from .score import ScoreRepository


class ReviewRepository:
    def __init__(
        self,
        session: Session,
        score_repository: ScoreRepository | None = None,
    ) -> None:
        self.session = session
        self.scores = score_repository or ScoreRepository(session)

    def list_public(
        self, school_id: int, *, limit: int = 20, offset: int = 0
    ) -> list[Review]:
        statement = (
            select(Review)
            .where(Review.school_id == school_id, Review.is_hidden.is_(False))
            .options(selectinload(Review.scores), selectinload(Review.user))
            .order_by(
                Review.user_id.is_(None),
                Review.created_at.desc(),
                Review.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement).all())

    def get_by_id(self, review_id: int) -> Review | None:
        statement = (
            select(Review)
            .where(Review.id == review_id)
            .options(selectinload(Review.scores))
        )

        return self.session.scalar(statement)

    def get_user_review(self, school_id: int, user_id: int) -> Review | None:
        statement = (
            select(Review)
            .where(
                Review.school_id == school_id,
                Review.user_id == user_id,
            )
            .options(selectinload(Review.scores))
        )

        return self.session.scalar(statement)

    def create(
        self,
        *,
        school_id: int,
        scores: list[tuple[Group, int]],
        observation: str | None = None,
        user_id: int | None = None,
    ) -> Review:
        self._require_active_school(school_id)

        review = Review(
            school_id=school_id,
            user_id=user_id,
            observation=observation,
            scores=[
                ReviewGroupScore(group=group, score=score)
                for group, score in scores
            ],
        )

        self.session.add(review)
        self.session.flush()

        for group, score in scores:
            self.scores.record_review_score(school_id, group, score)

        self.session.flush()
        return review

    def update(
        self,
        *,
        school_id: int,
        user_id: int,
        scores: list[tuple[Group, int]],
        observation: str | None = None,
    ) -> Review:
        review = self.get_user_review(school_id, user_id)
        if review is None:
            raise ReviewNotFound(school_id, user_id)

        old_scores = {item.group: item.score for item in review.scores}
        new_scores = dict(scores)

        if not review.is_hidden:
            deltas = self._build_score_deltas(old_scores, new_scores)
            for group, (delta_count, delta_sum) in deltas.items():
                self.scores.apply_delta(
                    school_id,
                    group,
                    d_count=delta_count,
                    d_sum=delta_sum,
                )

        review.scores[:] = [
            ReviewGroupScore(group=group, score=score)
            for group, score in scores
        ]
        review.observation = observation

        self.session.flush()
        return review

    @staticmethod
    def _build_score_deltas(
        old_scores: dict[Group, int],
        new_scores: dict[Group, int],
    ) -> dict[Group, tuple[int, int]]:
        """Calculate wallet count and sum changes for each affected group."""
        count_delta_by_presence = {
            (True, True): 0,
            (True, False): -1,
            (False, True): 1,
        }

        return {
            group: (
                count_delta_by_presence[
                    (group in old_scores, group in new_scores)
                ],
                new_scores.get(group, 0) - old_scores.get(group, 0),
            )
            for group in old_scores.keys() | new_scores.keys()
        }

    def delete_user_review(self, *, school_id: int, user_id: int) -> None:
        review = self.get_user_review(school_id, user_id)

        if review is None:
            raise ReviewNotFound(school_id, user_id)

        if not review.is_hidden:
            for score in review.scores:
                self.scores.apply_delta(
                    school_id,
                    score.group,
                    d_count=-1,
                    d_sum=-score.score,
                )

        self.session.delete(review)
        self.session.flush()

    def set_hidden(self, review: Review, is_hidden: bool) -> None:
        if review.is_hidden == is_hidden:
            return

        delta_by_visibility = {True: -1, False: 1}
        delta = delta_by_visibility[is_hidden]

        for score in review.scores:
            self.scores.apply_delta(
                review.school_id,
                score.group,
                d_count=delta,
                d_sum=delta * score.score,
            )

        review.is_hidden = is_hidden
        self.session.flush()

    def _require_active_school(self, school_id: int) -> School:
        statement = select(School).where(
            School.id == school_id, School.is_active.is_(True)
        )

        school = self.session.scalar(statement)

        if school is None:
            raise SchoolNotFound(school_id)
        return school
