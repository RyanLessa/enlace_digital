import unicodedata
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import Select

from enlace_digital.interface.models import (
    Group,
    Neighborhood,
    School,
    SchoolGroupScore,
)
from enlace_digital.interface.repositories.exceptions import SchoolNotFound

RANKING_PRIOR_MEAN = 3.0
RANKING_PRIOR_WEIGHT = 5.0
MIN_REVIEWS_TO_DISPLAY = 1


@dataclass(frozen=True)
class SchoolSearchResult:
    school: School
    matched_groups: tuple[Group, ...]
    ranking_score: float | None


@dataclass(frozen=True)
class SchoolGroupScoreProfile:
    group: Group
    has_adaptation: bool
    average: float | None
    review_count: int


@dataclass(frozen=True)
class SchoolProfile:
    school: School
    neighborhood: Neighborhood
    scores: tuple[SchoolGroupScoreProfile, ...]


class SchoolRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        *,
        neighborhood_id: int | None = None,
        groups: list[Group] | None = None,
        query: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SchoolSearchResult]:
        selected_groups = list(dict.fromkeys(groups or []))
        ranking = self._build_ranking_value()
        statement = self._build_unfiltered_groups_statement(ranking=ranking)
        if selected_groups:
            statement = self._build_selected_groups_statement(
                selected_groups=selected_groups,
                ranking=ranking,
            )

        statement = self._apply_search_filters(
            statement,
            neighborhood_id=neighborhood_id,
            query=query,
        )
        rows = self.session.execute(statement.limit(limit).offset(offset)).all()
        return self._build_search_results(rows, selected_groups)

    @staticmethod
    def _build_ranking_value():
        """Build the Bayesian-smoothed score expression used in school ranking."""
        return (
            RANKING_PRIOR_WEIGHT * RANKING_PRIOR_MEAN
            + SchoolGroupScore.score_sum
        ) / (RANKING_PRIOR_WEIGHT + SchoolGroupScore.review_count)

    @staticmethod
    def _build_selected_groups_statement(
        *,
        selected_groups: list[Group],
        ranking: Any,
    ) -> Select[Any]:
        """Build a query ranking schools by how many selected groups they support."""
        matched_scores = (
            select(
                SchoolGroupScore.school_id.label("school_id"),
                func.count(SchoolGroupScore.group).label("matched_count"),
                func.avg(ranking).label("ranking_score"),
            )
            .where(
                SchoolGroupScore.group.in_(selected_groups),
                SchoolGroupScore.has_adaptation.is_(True),
            )
            .group_by(SchoolGroupScore.school_id)
            .subquery()
        )
        return (
            select(
                School,
                matched_scores.c.matched_count,
                matched_scores.c.ranking_score,
            )
            .join(matched_scores, matched_scores.c.school_id == School.id)
            .options(selectinload(School.scores), selectinload(School.neighborhood))
            .order_by(
                matched_scores.c.matched_count.desc(),
                matched_scores.c.ranking_score.desc().nullslast(),
                School.id,
            )
        )

    @staticmethod
    def _build_unfiltered_groups_statement(ranking: Any) -> Select[Any]:
        """Build a query ranking active schools without requiring group matches."""
        school_scores = (
            select(
                SchoolGroupScore.school_id.label("school_id"),
                func.avg(ranking).label("ranking_score"),
            )
            .group_by(SchoolGroupScore.school_id)
            .subquery()
        )
        return (
            select(
                School,
                literal(0).label("matched_count"),
                school_scores.c.ranking_score,
            )
            .outerjoin(school_scores, school_scores.c.school_id == School.id)
            .options(selectinload(School.scores), selectinload(School.neighborhood))
            .order_by(
                school_scores.c.ranking_score.desc().nullslast(),
                School.id,
            )
        )

    @staticmethod
    def _apply_search_filters(
        statement: Select[Any],
        *,
        neighborhood_id: int | None,
        query: str | None,
    ) -> Select[Any]:
        statement = statement.where(School.is_active.is_(True))
        if neighborhood_id is not None:
            statement = statement.where(School.neighborhood_id == neighborhood_id)
        normalized_query = SchoolRepository._normalize_name(query)
        if normalized_query:
            statement = statement.where(
                School.name_normalized.contains(normalized_query)
            )
        return statement

    @staticmethod
    def _build_search_results(
        rows: list[Any],
        selected_groups: list[Group],
    ) -> list[SchoolSearchResult]:
        """Map query rows to search results while preserving requested group order."""
        results: list[SchoolSearchResult] = []
        for school, _, ranking_score in rows:
            adapted_groups = {
                score.group for score in school.scores if score.has_adaptation
            }
            matched_groups = tuple(
                group for group in selected_groups if group in adapted_groups
            )
            results.append(
                SchoolSearchResult(
                    school=school,
                    matched_groups=matched_groups,
                    ranking_score=SchoolRepository._to_optional_float(ranking_score),
                )
            )
        return results

    @staticmethod
    def _to_optional_float(value: Any) -> float | None:
        if value is None:
            return None
        return float(value)

    def get_profile(self, school_id: int) -> SchoolProfile:
        statement = (
            select(School)
            .where(School.id == school_id, School.is_active.is_(True))
            .options(
                selectinload(School.neighborhood),
                selectinload(School.scores),
            )
        )
        school = self.session.scalar(statement)
        if school is None:
            raise SchoolNotFound(school_id)

        return SchoolProfile(
            school=school,
            neighborhood=school.neighborhood,
            scores=self._build_profile_scores(school.scores),
        )

    @staticmethod
    def _build_profile_scores(
        school_scores: list[SchoolGroupScore],
    ) -> tuple[SchoolGroupScoreProfile, ...]:
        """Build ordered wallet entries, hiding averages below the minimum."""
        group_order = {group: index for index, group in enumerate(Group)}
        return tuple(
            SchoolGroupScoreProfile(
                group=score.group,
                has_adaptation=score.has_adaptation,
                average=SchoolRepository._build_display_average(score),
                review_count=score.review_count,
            )
            for score in sorted(
                school_scores,
                key=lambda item: group_order[item.group],
            )
        )

    @staticmethod
    def _build_display_average(score: SchoolGroupScore) -> float | None:
        if score.review_count < MIN_REVIEWS_TO_DISPLAY:
            return None
        return min(5.0, max(1.0, score.score_sum / score.review_count))

    def get_by_id(self, school_id: int) -> School | None:
        statement = (
            select(School)
            .where(School.id == school_id)
            .options(selectinload(School.scores), selectinload(School.neighborhood))
        )
        return self.session.scalar(statement)

    def upsert(
        self,
        *,
        name: str,
        neighborhood_id: int,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        groups: list[Group] | None = None,
    ) -> School:
        normalized_name = self._normalize_name(name)
        statement = select(School).where(
            School.name_normalized == normalized_name,
            School.neighborhood_id == neighborhood_id,
        )
        school = self.session.scalar(statement)
        if school is not None:
            return self._update_school(
                school,
                name=name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                groups=groups,
            )

        school = School(
            name=name.strip(),
            name_normalized=normalized_name,
            neighborhood_id=neighborhood_id,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        self.session.add(school)
        self.session.flush()
        self._synchronize_adaptation_groups(school, groups)
        self.session.flush()
        return school

    def _update_school(
        self,
        school: School,
        *,
        name: str,
        address: str | None,
        latitude: float | None,
        longitude: float | None,
        groups: list[Group] | None,
    ) -> School:
        """Update an existing school and synchronize its group adaptations."""
        school.name = name.strip()
        school.address = address
        school.latitude = latitude
        school.longitude = longitude
        school.is_active = True
        self._synchronize_adaptation_groups(school, groups)
        self.session.flush()
        return school

    def _synchronize_adaptation_groups(
        self,
        school: School,
        groups: list[Group] | None,
    ) -> None:
        """Ensure one wallet row per group and synchronize adaptation flags."""
        adaptations = set(groups or [])
        existing_scores = {score.group: score for score in school.scores}
        for group in Group:
            score = existing_scores.get(group)
            if score is None:
                score = SchoolGroupScore(school=school, group=group)
                self.session.add(score)
            score.has_adaptation = group in adaptations

    @staticmethod
    def _normalize_name(name: str | None) -> str:
        if name is None:
            return ""
        decomposed = unicodedata.normalize("NFKD", name.strip().casefold())
        return "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        )
