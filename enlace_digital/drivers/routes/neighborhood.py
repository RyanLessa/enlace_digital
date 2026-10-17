from fastapi import APIRouter
from fastapi.responses import JSONResponse

from enlace_digital.interface.controllers import NeighborhoodController

router = APIRouter(prefix="/neighborhoods", tags=["neighborhoods"])
controller = NeighborhoodController()


@router.get("")
def list_neighborhoods() -> JSONResponse:
    result = controller.list_all()
    return JSONResponse(status_code=result.status_code, content=result.content)
