from fastapi import Depends
from sqlalchemy.orm import Session

from enlace_digital.interface.controllers import (
    NeighborhoodController,
    ReviewController,
    SchoolController,
    UserController,
)
from enlace_digital.settings.get_db import get_db
from enlace_digital.use_cases.services import (
    NeighborhoodService,
    ReviewService,
    SchoolService,
    UserService,
)


def get_school_controller(
    session: Session = Depends(get_db),
) -> SchoolController:
    return SchoolController(SchoolService(session))


def get_review_controller(
    session: Session = Depends(get_db),
) -> ReviewController:
    return ReviewController(ReviewService(session))


def get_neighborhood_controller(
    session: Session = Depends(get_db),
) -> NeighborhoodController:
    return NeighborhoodController(NeighborhoodService(session))


def get_user_controller(session: Session = Depends(get_db)) -> UserController:
    return UserController(UserService(session))
