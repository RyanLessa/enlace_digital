from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from enlace_digital.drivers.presenters import UserCreatePresenter, UserLoginPresenter
from enlace_digital.interface.controllers import UserController

from .dependencies import get_user_controller

router = APIRouter(prefix="/auth", tags=["users"])


@router.post("/register")
def register_user(
    payload: UserCreatePresenter,
    controller: UserController = Depends(get_user_controller),
) -> JSONResponse:
    result = controller.register(email=payload.email, password=payload.password)
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.post("/login")
def login_user(
    payload: UserLoginPresenter,
    controller: UserController = Depends(get_user_controller),
) -> JSONResponse:
    result = controller.login(email=payload.email, password=payload.password)
    return JSONResponse(status_code=result.status_code, content=result.content)
