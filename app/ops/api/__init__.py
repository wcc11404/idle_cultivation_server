from fastapi import APIRouter

from . import AuthApi, PlayerApi, GrantApi, SystemApi, AuditApi

router = APIRouter()
router.include_router(AuthApi.router)
router.include_router(PlayerApi.router)
router.include_router(GrantApi.router)
router.include_router(SystemApi.router)
router.include_router(AuditApi.router)
