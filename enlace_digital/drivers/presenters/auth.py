import re
from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from .base import Presenter


class RegisterPresenter(Presenter):
    email: str = Field(strict=True, max_length=254)
    password: str = Field(strict=True, min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        email = email.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Informe um e-mail válido.")
        return email


class LoginPresenter(Presenter):
    email: str = Field(strict=True, max_length=254)
    password: str = Field(strict=True, min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        email = email.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Informe um e-mail válido.")
        return email


class AccessTokenPresenter(Presenter):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserCreatedPresenter(Presenter):
    id: int
    created_at: datetime
