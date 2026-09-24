from fastapi import APIRouter

from app.api.routes.compositions import (
    router as compositions_router,
)
from app.api.routes.health import (
    router as health_router,
)


router = APIRouter()

router.include_router(health_router)
router.include_router(compositions_router)