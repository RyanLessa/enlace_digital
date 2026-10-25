from datetime import datetime

from pydantic import Field

from .auth import LoginPresenter, RegisterPresenter
from .base import Presenter


class UserCreatePresenter(RegisterPresenter):
    name: str


class UserLoginPresenter(LoginPresenter):
    pass


class UserPresenter(Presenter):
    id: int
    name: str
    created_at: datetime


class UserListParams(Presenter):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
