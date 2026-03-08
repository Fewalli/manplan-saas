from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.tenant import router as tenant_router
from app.api.routes.users import router as users_router
from app.api.v1.areas import router as areas_router
from app.api.v1.assets import router as assets_router
from app.api.v1.work_orders import router as work_orders_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(tenant_router)
api_router.include_router(users_router)
api_router.include_router(areas_router)
api_router.include_router(assets_router)
api_router.include_router(work_orders_router)