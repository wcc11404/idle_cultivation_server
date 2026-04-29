from fastapi import APIRouter
from app.api import GameBase, Admin, Test
from app.modules.spell import SpellApi
from app.modules.inventory import InventoryApi
from app.modules.alchemy import AlchemyApi
from app.modules.lianli import LianliApi
from app.modules.herb.HerbApi import router as herb_router
from app.modules.task.TaskApi import router as task_router
from app.modules.mail.MailApi import router as mail_router
from app.modules.cultivation import CultivationApi
from app.modules.account.AccountApi import router as account_router

api_router = APIRouter()

api_router.include_router(account_router, prefix="/auth", tags=["auth"])
api_router.include_router(GameBase.router, prefix="/game", tags=["game_base"])
api_router.include_router(CultivationApi.router, prefix="/game", tags=["cultivation"])
api_router.include_router(SpellApi.router, prefix="/game", tags=["spell"])
api_router.include_router(InventoryApi.router, prefix="/game", tags=["inventory"])
api_router.include_router(AlchemyApi.router, prefix="/game", tags=["alchemy"])
api_router.include_router(LianliApi.router, prefix="/game", tags=["lianli"])
api_router.include_router(herb_router, prefix="/game", tags=["herb"])
api_router.include_router(task_router, prefix="/game", tags=["task"])
api_router.include_router(mail_router, prefix="/game", tags=["mail"])
api_router.include_router(Admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(Test.router, prefix="/test", tags=["test"])
