from fastapi import APIRouter
from app.api import auth, game_base, admin
from app.modules.spell import SpellApi
from app.modules.inventory import InventoryApi
from app.modules.alchemy import AlchemyApi
from app.modules.lianli import LianliApi
from app.modules.cultivation import CultivationApi

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(game_base.router, prefix="/game", tags=["game_base"])
api_router.include_router(CultivationApi.router, prefix="/game", tags=["cultivation"])
api_router.include_router(SpellApi.router, prefix="/game", tags=["spell"])
api_router.include_router(InventoryApi.router, prefix="/game", tags=["inventory"])
api_router.include_router(AlchemyApi.router, prefix="/game", tags=["alchemy"])
api_router.include_router(LianliApi.router, prefix="/game", tags=["lianli"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
