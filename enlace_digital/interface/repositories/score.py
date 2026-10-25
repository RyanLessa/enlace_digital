from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from enlace_digital.interface.models import (
    Group,
    Review,
    ReviewGroupScore,
    School,
    SchoolGroupScore,
)

from .exceptions import SchoolNotFound, SchoolScoreNotFound


class ScoreRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record_review_score(
        self, school_id: int, group: Group, score: int
    ) -> None:
        statement = (
            update(SchoolGroupScore)
            .where(
                SchoolGroupScore.school_id == school_id,
                SchoolGroupScore.group == group,
            )
            .values(
                review_count=SchoolGroupScore.review_count + 1,
                score_sum=SchoolGroupScore.score_sum + score,
            )
        )
        result = self.session.execute(statement)
        if result.rowcount != 1:
            raise SchoolScoreNotFound(school_id, group)

    def apply_delta(
        self,
        school_id: int,
        group: Group,
        *,
        d_count: int,
        d_sum: int,
    ) -> None:
        statement = (
            update(SchoolGroupScore)
            .where(
                SchoolGroupScore.school_id == school_id,
                SchoolGroupScore.group == group,
            )
            .values(
                review_count=SchoolGroupScore.review_count + d_count,
                score_sum=SchoolGroupScore.score_sum + d_sum,
            )
        )
        result = self.session.execute(statement)
        if result.rowcount != 1:
            raise SchoolScoreNotFound(school_id, group)

    def recalculate_school_scores(self, school_id: int) -> None:
        if self.session.get(School, school_id) is None:
            raise SchoolNotFound(school_id)

        existing_groups = set(self._list_school_groups(school_id))
        missing_groups = [group for group in Group if group not in existing_groups]
        if missing_groups:
            raise SchoolScoreNotFound(school_id, missing_groups[0])

        aggregates = self._build_school_score_aggregates(school_id)
        statement = self._build_recalculation_statement(school_id, aggregates)
        self.session.execute(statement)
        self.session.flush()

    def _list_school_groups(self, school_id: int) -> list[Group]:
        """Return the groups currently represented in a school's score wallet."""
        statement = select(SchoolGroupScore.group).where(
            SchoolGroupScore.school_id == school_id
        )
        return list(self.session.scalars(statement))

    @staticmethod
    def _build_school_score_aggregates(school_id: int):
        """Aggregate counts and sums from visible review scores by group."""
        return (
            select(
                ReviewGroupScore.group.label("group"),
                func.count(Review.id).label("review_count"),
                func.coalesce(func.sum(ReviewGroupScore.score), 0).label(
                    "score_sum"
                ),
            )
            .join(Review, Review.id == ReviewGroupScore.review_id)
            .where(Review.school_id == school_id, Review.is_hidden.is_(False))
            .group_by(ReviewGroupScore.group)
            .subquery()
        )

    @staticmethod
    def _build_recalculation_statement(school_id: int, aggregates):
        """Build one update that replaces wallet totals with the aggregates."""
        return (
            update(SchoolGroupScore)
            .where(SchoolGroupScore.school_id == school_id)
            .values(
                review_count=func.coalesce(
                    select(aggregates.c.review_count)
                    .where(aggregates.c.group == SchoolGroupScore.group)
                    .correlate(SchoolGroupScore)
                    .scalar_subquery(),
                    0,
                ),
                score_sum=func.coalesce(
                    select(aggregates.c.score_sum)
                    .where(aggregates.c.group == SchoolGroupScore.group)
                    .correlate(SchoolGroupScore)
                    .scalar_subquery(),
                    0,
                ),
            )
        )
