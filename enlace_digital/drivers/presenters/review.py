from datetime import datetime

from pydantic import AliasChoices, Field, field_validator

from enlace_digital.interface.models.enums import Group, NOTA_MAX, NOTA_MIN

from .base import Presenter


class ReviewScorePresenter(Presenter):
    group: Group
    score: int = Field(strict=True, ge=NOTA_MIN, le=NOTA_MAX)


class ReviewCreatePresenter(Presenter):
    scores: list[ReviewScorePresenter] = Field(min_length=1, max_length=5)
    observation: str | None = None

    @field_validator("scores")
    @classmethod
    def validate_unique_groups(
        cls, scores: list[ReviewScorePresenter]
    ) -> list[ReviewScorePresenter]:
        groups = [score.group for score in scores]
        if len(groups) != len(set(groups)):
            raise ValueError("Cada grupo pode aparecer apenas uma vez.")
        return scores


class ReviewUpdatePresenter(ReviewCreatePresenter):
    pass


class ReviewPresenter(Presenter):
    id: int
    school_id: int
    created_at: datetime
    observation: str | None = None
    from_registered_user: bool = Field(
        validation_alias=AliasChoices("from_registered_user", "user_id")
    )
    scores: list[ReviewScorePresenter]

    @field_validator("from_registered_user", mode="before")
    @classmethod
    def hide_user_identity(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        return value is not None


class ReviewListPresenter(Presenter):
    items: list[ReviewPresenter]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class ReviewListParams(Presenter):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
