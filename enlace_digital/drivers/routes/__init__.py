from fastapi import APIRouter

from .neighborhood import router as neighborhood_router
from .review import router as review_router
from .school import router as school_router
from .user import users_router

router = APIRouter()
router.include_router(school_router)
router.include_router(review_router)
router.include_router(neighborhood_router)
router.include_router(users_router)

__all__ = ["router"]