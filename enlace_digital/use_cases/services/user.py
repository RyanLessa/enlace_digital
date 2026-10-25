import os
from typing import Any

import jwt
from jwt.exceptions import JWTDecodeError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from enlace_digital.interface.models import User
from enlace_digital.interface.repositories import UserRepository

from .base import ServiceResult
from .security import (
    JWT_ALGORITHM,
    SECRET_KEY,
    create_access_token,
    hash_password,
    verify_password,
)


class UserService:
    def __init__(
        self,
        session: Session,
        repository: UserRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or UserRepository(session)

    def register(
        self, *, name: str, email: str, password: str
    ) -> ServiceResult:
        normalized_email = email.strip().casefold()
        if self.repository.get_by_email(normalized_email) is not None:
            return ServiceResult(
                409,
                {"detail": "Já existe uma conta com esse e-mail"},
            )

        try:
            password_hash = hash_password(password)
        except ValueError:
            return ServiceResult(
                422,
                {"detail": "Senha grande demais. O limite é de 72 bytes."},
            )

        try:
            user = self.repository.create(
                name=name,
                email=normalized_email,
                password_hash=password_hash,
            )
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            if self._is_duplicate_email(error):
                return ServiceResult(
                    409,
                    {"detail": "Já existe uma conta com esse e-mail"},
                )
            raise
        except Exception:
            self.session.rollback()
            raise

        return ServiceResult(201, self._present_user(user))

    def login(self, *, email: str, password: str) -> ServiceResult:
        user = self.repository.get_by_email(email.strip().casefold())

        if user is None or not verify_password(password, user.password_hash):
            return ServiceResult(401, {"detail": "E-mail ou senha inválidos."})

        return ServiceResult(
            200,
            {
                "access_token": create_access_token(user.id),
                "token_type": "bearer",
            },
        )

    def list_users(self, *, limit: int, offset: int) -> ServiceResult:
        users = self.repository.list_users(limit=limit, offset=offset)
        return ServiceResult(
            200,
            {
                "items": [self._present_user(user) for user in users],
                "limit": limit,
                "offset": offset,
            },
        )

    def get_by_id(self, user_id: int) -> ServiceResult:
        user = self.repository.get_by_id(user_id)
        if user is None:
            return ServiceResult(404, {"detail": "Usuário não encontrado."})
        return ServiceResult(200, self._present_user(user))

    @staticmethod
    def decode_payload(payload: str) -> int | None:
        signing_key = jwt.jwk.OctetJWK(
            SECRET_KEY.encode(),
            alg=JWT_ALGORITHM,
        )
        try:
            decoded = jwt.JWT().decode(
                payload,
                key=signing_key,
                algorithms={JWT_ALGORITHM},
            )
        except JWTDecodeError:
            return None

        if not isinstance(decoded, dict):
            return None
        user_id = decoded.get("id")
        if type(user_id) is not int or user_id <= 0:
            return None

        return user_id

    @staticmethod
    def _present_user(user: User) -> dict[str, Any]:
        return {
            "id": user.id,
            "name": user.name,
            "created_at": user.created_at.isoformat(),
        }

    @staticmethod
    def _is_duplicate_email(error: IntegrityError) -> bool:
        return "UNIQUE constraint failed: users.email" in str(error.orig)
