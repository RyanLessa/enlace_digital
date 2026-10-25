from datetime import datetime

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
