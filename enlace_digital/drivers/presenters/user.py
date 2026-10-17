from datetime import datetime

from .auth import LoginPresenter, RegisterPresenter
from .base import Presenter


class UserCreatePresenter(RegisterPresenter):
    pass


class UserLoginPresenter(LoginPresenter):
    pass


class UserPresenter(Presenter):
    id: int
    created_at: datetime
