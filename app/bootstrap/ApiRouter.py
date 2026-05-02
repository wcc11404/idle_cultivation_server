from fastapi import APIRouter

from app.admin_support.api import router as admin_router
from app.game.api import api_router as game_api_router
from app.ops.api import router as ops_router
from app.test_support.api import router as test_router

api_router = APIRouter()
api_router.include_router(game_api_router)
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(test_router, prefix="/test", tags=["test"])

ops_api_router = APIRouter()
ops_api_router.include_router(ops_router, prefix="/api", tags=["ops"])
