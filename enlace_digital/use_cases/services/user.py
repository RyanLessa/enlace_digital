from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from enlace_digital.interface.models import User
from enlace_digital.interface.repositories import UserRepository

from .base import ServiceResult
from .security import create_access_token, hash_password, verify_password


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
                {"detail": "An account with this email already exists."},
            )

        try:
            password_hash = hash_password(password)
        except ValueError:
            return ServiceResult(
                422,
                {"detail": "Password must not exceed 72 UTF-8 bytes."},
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
                    {"detail": "An account with this email already exists."},
                )
            raise
        except Exception:
            self.session.rollback()
            raise

        return ServiceResult(201, self._present_user(user))

    def login(self, *, email: str, password: str) -> ServiceResult:
        user = self.repository.get_by_email(email.strip().casefold())

        if user is None or not verify_password(password, user.password_hash):
            return ServiceResult(401, {"detail": "Invalid email or password."})

        return ServiceResult(
            200,
            {
                "access_token": create_access_token(user.id),
                "token_type": "bearer",
            },
        )

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
