from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from enlace_digital.drivers.authentication import get_user_id
from enlace_digital.drivers.presenters import (
    UserCreatePresenter,
    UserListParams,
    UserLoginPresenter,
)
from enlace_digital.interface.controllers import UserController

from .dependencies import get_user_controller

auth_router = APIRouter(prefix="/auth", tags=["users"])
router = APIRouter(prefix="/users", tags=["users"])


@auth_router.post("/register")
def register_user(
    payload: UserCreatePresenter,
    controller: UserController = Depends(get_user_controller),
) -> JSONResponse:
    result = controller.register(
        name=payload.name,
        email=payload.email,
        password=payload.password,
    )
    return JSONResponse(status_code=result.status_code, content=result.content)


@auth_router.post("/login")
def login_user(
    payload: UserLoginPresenter,
    controller: UserController = Depends(get_user_controller),
) -> JSONResponse:
    result = controller.login(email=payload.email, password=payload.password)
    return JSONResponse(status_code=result.status_code, content=result.content)


@auth_router.get("/whoami")
def whoami(
    user_id: int | None = Depends(get_user_id),
    controller: UserController = Depends(get_user_controller),
) -> JSONResponse:
    if user_id is None:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token de autenticação inválido ou ausente."},
        )

    result = controller.get_by_id(user_id)
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.get("")
def list_users(
    params: UserListParams = Depends(),
    controller: UserController = Depends(get_user_controller),
) -> JSONResponse:
    result = controller.list_users(limit=params.limit, offset=params.offset)
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.get("/{user_id}")
def get_user(
    user_id: int = Path(gt=0),
    controller: UserController = Depends(get_user_controller),
) -> JSONResponse:
    result = controller.get_by_id(user_id)
    return JSONResponse(status_code=result.status_code, content=result.content)


users_router = APIRouter()
users_router.include_router(auth_router)
users_router.include_router(router)
