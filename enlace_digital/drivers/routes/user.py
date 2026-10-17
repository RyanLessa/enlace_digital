from fastapi import APIRouter
from fastapi.responses import JSONResponse

from enlace_digital.drivers.presenters import UserCreatePresenter, UserLoginPresenter
from enlace_digital.interface.controllers import UserController

router = APIRouter(prefix="/auth", tags=["users"])
controller = UserController()


@router.post("/register")
def register_user(payload: UserCreatePresenter) -> JSONResponse:
    result = controller.register(email=payload.email, password=payload.password)
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.post("/login")
def login_user(payload: UserLoginPresenter) -> JSONResponse:
    result = controller.login(email=payload.email, password=payload.password)
    return JSONResponse(status_code=result.status_code, content=result.content)
