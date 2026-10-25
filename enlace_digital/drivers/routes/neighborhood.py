from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from enlace_digital.drivers.presenters import NeighborhoodListParams
from enlace_digital.interface.controllers import NeighborhoodController

from .dependencies import get_neighborhood_controller

router = APIRouter(prefix="/neighborhoods", tags=["neighborhoods"])


@router.get("")
def list_neighborhoods(
    params: NeighborhoodListParams = Depends(),
    controller: NeighborhoodController = Depends(get_neighborhood_controller),
) -> JSONResponse:
    result = controller.list_all(limit=params.limit)
    return JSONResponse(status_code=result.status_code, content=result.content)
