from pydantic import Field, field_validator

from enlace_digital.interface.models.enums import Group

from .base import Presenter
from .neighborhood import NeighborhoodPresenter


class SchoolSearchParams(Presenter):
    neighborhood_id: int | None = Field(default=None, ge=1)
    groups: list[Group] = Field(default=[], max_length=5)
    q: str | None = Field(default=None, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("groups", mode="before")
    @classmethod
    def split_groups(cls, groups: object) -> object:
        if isinstance(groups, str):
            return [group.strip() for group in groups.split(",") if group.strip()]

        return groups

    @field_validator("groups")
    @classmethod
    def validate_unique_groups(cls, groups: list[Group]) -> list[Group]:
        if len(groups) != len(set(groups)):
            raise ValueError("Cada grupo pode aparecer apenas uma vez.")

        return groups

    @field_validator("q")
    @classmethod
    def strip_search_text(cls, query: str | None) -> str | None:
        if query is None:
            return None

        query = query.strip()

        return query or None


class SchoolGroupScorePresenter(Presenter):
    group: Group
    average: float | None
    review_count: int = Field(ge=0)


class SchoolPresenter(Presenter):
    id: int
    name: str
    neighborhood: NeighborhoodPresenter
    address: str | None
    scores: list[SchoolGroupScorePresenter]


class SchoolSearchItemPresenter(Presenter):
    id: int
    name: str
    address: str | None
    matched_groups: list[Group]
    ranking_score: float | None


class SchoolSearchPresenter(Presenter):
    items: list[SchoolSearchItemPresenter]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
