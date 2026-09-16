from fastapi import APIRouter

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.dashboard.routes import router as dashboard_router
from app.api.v1.health.routes import router as health_router
from app.api.v1.raffle.routes import router as raffle_router
from app.api.v1.sales.routes import router as sales_router
from app.api.v1.users.routes import router as users_router
from app.core.config import settings

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(raffle_router)
router.include_router(sales_router)
router.include_router(users_router)
router.include_router(dashboard_router)

if not settings.is_production:
    from app.api.v1.ui.routes import router as ui_router

    router.include_router(ui_router)
