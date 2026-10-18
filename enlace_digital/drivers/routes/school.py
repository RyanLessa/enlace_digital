from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from enlace_digital.drivers.presenters import SchoolSearchParams
from enlace_digital.interface.controllers import SchoolController

from .dependencies import get_school_controller

router = APIRouter(prefix="/schools", tags=["schools"])


@router.get("")
def search_schools(
    params: SchoolSearchParams = Depends(),
    controller: SchoolController = Depends(get_school_controller),
) -> JSONResponse:
    result = controller.search(
        neighborhood_id=params.neighborhood_id,
        groups=params.groups,
        query=params.q,
        limit=params.limit,
        offset=params.offset,
    )
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.get("/{school_id}")
def get_school(
    school_id: int = Path(gt=0),
    controller: SchoolController = Depends(get_school_controller),
) -> JSONResponse:
    result = controller.get_by_id(school_id)
    return JSONResponse(status_code=result.status_code, content=result.content)
