from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/neighborhoods", tags=["neighborhoods"])


@router.get("")
def list_neighborhoods() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"detail": "Neighborhood listing is not implemented yet."},
    )
