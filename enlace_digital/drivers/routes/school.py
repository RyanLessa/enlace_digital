from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from enlace_digital.drivers.presenters import SchoolSearchParams

router = APIRouter(prefix="/schools", tags=["schools"])


@router.get("")
def search_schools(params: SchoolSearchParams = Depends()) -> JSONResponse:
    del params
    return JSONResponse(
        status_code=501,
        content={"detail": "School search is not implemented yet."},
    )


@router.get("/{school_id}")
def get_school(school_id: int = Path(gt=0)) -> JSONResponse:
    del school_id
    return JSONResponse(
        status_code=501,
        content={"detail": "School details are not implemented yet."},
    )
