from pydantic import Field

from .base import Presenter


class NeighborhoodPresenter(Presenter):
    id: int
    name: str
    municipality: str
    slug: str


class NeighborhoodListParams(Presenter):
    limit: int = Field(default=100, ge=1, le=100)
