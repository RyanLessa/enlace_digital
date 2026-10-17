from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from enlace_digital.drivers.presenters import (
    ReviewCreatePresenter,
    ReviewListParams,
    ReviewUpdatePresenter,
)
from enlace_digital.interface.controllers import ReviewController

router = APIRouter(prefix="/schools/{school_id}/reviews", tags=["reviews"])
controller = ReviewController()


@router.get("")
def list_reviews(
    school_id: int = Path(gt=0),
    params: ReviewListParams = Depends(),
) -> JSONResponse:
    result = controller.list_for_school(
        school_id=school_id,
        limit=params.limit,
        offset=params.offset,
    )
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.post("")
def create_review(
    payload: ReviewCreatePresenter,
    school_id: int = Path(gt=0),
) -> JSONResponse:
    result = controller.create(
        school_id=school_id,
        scores=[(score.group, score.score) for score in payload.scores],
    )
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.put("/me")
def update_review(
    payload: ReviewUpdatePresenter,
    school_id: int = Path(gt=0),
) -> JSONResponse:
    result = controller.update(
        school_id=school_id,
        scores=[(score.group, score.score) for score in payload.scores],
    )
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.delete("/me")
def delete_review(school_id: int = Path(gt=0)) -> JSONResponse:
    result = controller.delete(school_id=school_id)
    return JSONResponse(status_code=result.status_code, content=result.content)
