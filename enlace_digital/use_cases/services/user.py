from .base import ServiceResult, not_implemented


class UserService:
    def register(self, *, email: str, password: str) -> ServiceResult:
        del email, password
        return not_implemented("User registration")

    def login(self, *, email: str, password: str) -> ServiceResult:
        del email, password
        return not_implemented("User login")
