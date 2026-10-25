from fastapi import APIRouter, Depends, Path, Response
from fastapi.responses import JSONResponse

from enlace_digital.drivers.authentication import get_user_id
from enlace_digital.drivers.presenters import (
    ReviewCreatePresenter,
    ReviewListParams,
    ReviewUpdatePresenter,
)
from enlace_digital.interface.controllers import ReviewController

from .dependencies import get_review_controller

router = APIRouter(prefix="/schools/{school_id}/reviews", tags=["reviews"])


@router.get("")
def list_reviews(
    school_id: int = Path(gt=0),
    params: ReviewListParams = Depends(),
    controller: ReviewController = Depends(get_review_controller),
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
    user_id: int | None = Depends(get_user_id),
    controller: ReviewController = Depends(get_review_controller),
) -> JSONResponse:
    result = controller.create(
        school_id=school_id,
        scores=[(score.group, score.score) for score in payload.scores],
        user_id=user_id,
        observation=payload.observation,
    )
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.put("/me")
def update_review(
    payload: ReviewUpdatePresenter,
    school_id: int = Path(gt=0),
    controller: ReviewController = Depends(get_review_controller),
) -> JSONResponse:
    result = controller.update(
        school_id=school_id,
        scores=[(score.group, score.score) for score in payload.scores],
        observation=payload.observation,
    )
    return JSONResponse(status_code=result.status_code, content=result.content)


@router.delete("/me")
def delete_review(
    school_id: int = Path(gt=0),
    controller: ReviewController = Depends(get_review_controller),
) -> Response:
    result = controller.delete(school_id=school_id)
    if result.status_code == 204:
        return Response(status_code=result.status_code)
    return JSONResponse(status_code=result.status_code, content=result.content)
