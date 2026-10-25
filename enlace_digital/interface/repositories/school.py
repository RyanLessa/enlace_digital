import unicodedata
from dataclasses import dataclass

from sqlalchemy import Float, and_, cast, func, select
from sqlalchemy.orm import Session, selectinload

from enlace_digital.interface.models import (
    Group,
    Neighborhood,
    School,
    SchoolGroupScore,
)
from enlace_digital.interface.repositories.exceptions import SchoolNotFound


@dataclass(frozen=True)
class SchoolSearchResult:
    school: School
    matched_groups: tuple[Group, ...]
    ranking_score: float | None


@dataclass(frozen=True)
class SchoolGroupScoreProfile:
    group: Group
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

    def exists_active(self, school_id: int) -> bool:
        statement = select(School.id).where(
            School.id == school_id,
            School.is_active.is_(True),
        )
        return self.session.scalar(statement) is not None

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
        score_join = [
            SchoolGroupScore.school_id == School.id,
            SchoolGroupScore.review_count > 0,
        ]
        if selected_groups:
            score_join.append(SchoolGroupScore.group.in_(selected_groups))

        group_average = (
            cast(SchoolGroupScore.score_sum, Float)
            / SchoolGroupScore.review_count
        )
        matched_count = func.count(SchoolGroupScore.group)
        statement = (
            select(School, matched_count, func.avg(group_average))
            .outerjoin(SchoolGroupScore, and_(*score_join))
            .where(School.is_active.is_(True))
            .options(selectinload(School.scores))
            .group_by(School.id)
        )
        if selected_groups:
            statement = statement.having(matched_count > 0)
        if neighborhood_id is not None:
            statement = statement.where(School.neighborhood_id == neighborhood_id)
        normalized_query = SchoolRepository._normalize_name(query)
        if normalized_query:
            statement = statement.where(
                School.name_normalized.contains(normalized_query)
            )
        ordering = [func.avg(group_average).desc().nullslast(), School.id]
        if selected_groups:
            ordering.insert(0, matched_count.desc())
        statement = statement.order_by(*ordering)

        rows = self.session.execute(
            statement.limit(limit).offset(offset)
        ).all()
        results: list[SchoolSearchResult] = []
        for school, _, ranking_score in rows:
            reviewed_groups = {
                score.group for score in school.scores if score.review_count > 0
            }
            matched_groups = tuple(
                group for group in selected_groups if group in reviewed_groups
            )
            results.append(
                SchoolSearchResult(
                    school=school,
                    matched_groups=matched_groups,
                    ranking_score=(
                        float(ranking_score) if ranking_score is not None else None
                    ),
                )
            )
        return results

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
        group_order = {group: index for index, group in enumerate(Group)}
        return tuple(
            SchoolGroupScoreProfile(
                group=score.group,
                average=score.average,
                review_count=score.review_count,
            )
            for score in sorted(
                school_scores,
                key=lambda item: group_order[item.group],
            )
        )

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
        self._ensure_wallet_rows(school)
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
    ) -> School:
        """Update the imported school fields and ensure its wallet is complete."""
        school.name = name.strip()
        school.address = address
        school.latitude = latitude
        school.longitude = longitude
        school.is_active = True
        self._ensure_wallet_rows(school)
        self.session.flush()
        return school

    def _ensure_wallet_rows(self, school: School) -> None:
        """Create any missing per-group score rows without changing existing scores."""
        existing_scores = {score.group: score for score in school.scores}
        school.scores.extend(
            SchoolGroupScore(group=group)
            for group in Group
            if group not in existing_scores
        )

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
