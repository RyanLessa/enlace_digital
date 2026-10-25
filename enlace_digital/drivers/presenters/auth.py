import re
from typing import Literal

from pydantic import Field, field_validator

from .base import Presenter

MAX_BCRYPT_PASSWORD_BYTES = 72


class RegisterPresenter(Presenter):
    email: str = Field(strict=True, max_length=254)
    password: str = Field(strict=True, min_length=8, max_length=1024)

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        email = email.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Informe um e-mail válido.")

        return email

    @field_validator("password")
    @classmethod
    def enforce_bcrypt_password_limit(cls, password: str) -> str:
        if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError("Senha grande demais. O limite é de 72 bytes.")

        return password


class LoginPresenter(Presenter):
    email: str = Field(strict=True, max_length=254)
    password: str = Field(strict=True, min_length=1, max_length=1024)

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        email = email.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Informe um e-mail válido.")

        return email

    @field_validator("password")
    @classmethod
    def enforce_bcrypt_password_limit(cls, password: str) -> str:
        if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError("Senha grande demais. O limite é de 72 bytes.")

        return password


class AccessTokenPresenter(Presenter):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
