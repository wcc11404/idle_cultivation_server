from fastapi import APIRouter
from app.api import auth, game, admin

api_router = APIRouter()

# 注册路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(game.router, prefix="/game", tags=["game"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])