from fastapi import APIRouter
from . import BaseApi, AuthApi, CultivationApi, SpellApi, InventoryApi, AlchemyApi, LianliApi, HerbApi, TaskApi, MailApi

api_router = APIRouter()
api_router.include_router(AuthApi.router, prefix="/auth", tags=["auth"])
api_router.include_router(BaseApi.router, prefix="/game", tags=["game_base"])
api_router.include_router(CultivationApi.router, prefix="/game", tags=["cultivation"])
api_router.include_router(SpellApi.router, prefix="/game", tags=["spell"])
api_router.include_router(InventoryApi.router, prefix="/game", tags=["inventory"])
api_router.include_router(AlchemyApi.router, prefix="/game", tags=["alchemy"])
api_router.include_router(LianliApi.router, prefix="/game", tags=["lianli"])
api_router.include_router(HerbApi.router, prefix="/game", tags=["herb"])
api_router.include_router(TaskApi.router, prefix="/game", tags=["task"])
api_router.include_router(MailApi.router, prefix="/game", tags=["mail"])
