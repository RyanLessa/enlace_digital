from fastapi import APIRouter
from fastapi.responses import JSONResponse

from enlace_digital.drivers.presenters import UserCreatePresenter, UserLoginPresenter

router = APIRouter(prefix="/auth", tags=["users"])


@router.post("/register")
def register_user(payload: UserCreatePresenter) -> JSONResponse:
    del payload
    return JSONResponse(
        status_code=501,
        content={"detail": "User registration is not implemented yet."},
    )


@router.post("/login")
def login_user(payload: UserLoginPresenter) -> JSONResponse:
    del payload
    return JSONResponse(
        status_code=501,
        content={"detail": "User login is not implemented yet."},
    )
