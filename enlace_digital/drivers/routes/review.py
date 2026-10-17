from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from enlace_digital.drivers.presenters import (
    ReviewCreatePresenter,
    ReviewListParams,
    ReviewUpdatePresenter,
)

router = APIRouter(prefix="/schools/{school_id}/reviews", tags=["reviews"])


@router.get("")
def list_reviews(
    school_id: int = Path(gt=0),
    params: ReviewListParams = Depends(),
) -> JSONResponse:
    del school_id, params
    return JSONResponse(
        status_code=501,
        content={"detail": "Review listing is not implemented yet."},
    )


@router.post("")
def create_review(
    payload: ReviewCreatePresenter,
    school_id: int = Path(gt=0),
) -> JSONResponse:
    del payload, school_id
    return JSONResponse(
        status_code=501,
        content={"detail": "Review creation is not implemented yet."},
    )


@router.put("/me")
def update_review(
    payload: ReviewUpdatePresenter,
    school_id: int = Path(gt=0),
) -> JSONResponse:
    del payload, school_id
    return JSONResponse(
        status_code=501,
        content={"detail": "Review updates are not implemented yet."},
    )


@router.delete("/me")
def delete_review(school_id: int = Path(gt=0)) -> JSONResponse:
    del school_id
    return JSONResponse(
        status_code=501,
        content={"detail": "Review deletion is not implemented yet."},
    )
