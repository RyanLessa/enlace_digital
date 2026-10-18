from enlace_digital.use_cases.services import ServiceResult, UserService


class UserController:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def register(self, *, email: str, password: str) -> ServiceResult:
        return self.service.register(email=email, password=password)

    def login(self, *, email: str, password: str) -> ServiceResult:
        return self.service.login(email=email, password=password)
