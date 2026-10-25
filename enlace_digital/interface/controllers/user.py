from enlace_digital.use_cases.services import ServiceResult, UserService


class UserController:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def register(
        self, *, name: str, email: str, password: str
    ) -> ServiceResult:
        return self.service.register(name=name, email=email, password=password)

    def login(self, *, email: str, password: str) -> ServiceResult:
        return self.service.login(email=email, password=password)

    def list_users(self, *, limit: int, offset: int) -> ServiceResult:
        return self.service.list_users(limit=limit, offset=offset)

    def get_by_id(self, user_id: int) -> ServiceResult:
        return self.service.get_by_id(user_id)
