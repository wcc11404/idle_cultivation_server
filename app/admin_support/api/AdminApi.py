from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from app.core.db.Models import Account, PlayerData
from app.core.security.Security import decode_token, verify_password, get_password_hash, create_access_token, security
from app.core.config.ServerConfig import settings
from app.core.logging.Logger import logger
from app.core.locks.WriteLock import begin_write_lock_by_account_id
from datetime import timedelta
from typing import List
import time
from app.game.domain.mail.MailSystem import MailSystem

router = APIRouter()


# 简化的管理员认证
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


class AdminMailAttachment(BaseModel):
    item_id: str
    count: int = Field(default=1, ge=1)


class AdminMailSendRequest(BaseModel):
    account_id: str
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    attachments: list[AdminMailAttachment] = Field(default_factory=list)


class AdminMailSendBatchRequest(BaseModel):
    account_ids: list[str] = Field(default_factory=list)
    all_accounts: bool = False
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    attachments: list[AdminMailAttachment] = Field(default_factory=list)


@router.post("/login", response_model=dict)
async def admin_login(username: str, password: str):
    """管理员登录"""
    start_time = time.time()
    logger.info(f"[IN] POST /admin/login - username: {username}")
    
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        logger.warning(f"[OUT] POST /admin/login - 用户名或密码错误 - username: {username} - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 生成管理员 token
    access_token_expires = timedelta(days=1)
    access_token = create_access_token(
        data={"admin": True},
        expires_delta=access_token_expires
    )
    
    logger.info(f"[OUT] POST /admin/login - 登录成功 - 耗时: {time.time() - start_time:.4f}s")
    return {
        "success": True,
        "token": access_token,
        "expires_in": int(access_token_expires.total_seconds())
    }


async def get_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取管理员"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or not payload.get("admin"):
        logger.warning("[ADMIN] 无效的管理员 token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的管理员 token"
        )
    
    return True


@router.get("/players", response_model=List[dict])
async def get_players(admin: bool = Depends(get_admin)):
    """获取玩家列表"""
    start_time = time.time()
    logger.info("[IN] GET /admin/players")
    
    accounts = await Account.all()
    players = []
    
    for account in accounts:
        player_data = await PlayerData.get_or_none(account_id=account.id)
        players.append({
            "id": str(account.id),
            "username": account.username,
            "server_id": account.server_id,
            "created_at": account.created_at.isoformat(),
            "last_online_at": player_data.updated_at.isoformat() if player_data else None
        })
    
    logger.info(f"[OUT] GET /admin/players - 获取成功 - 玩家数量: {len(players)} - 耗时: {time.time() - start_time:.4f}s")
    return players


@router.get("/player/{player_id}", response_model=dict)
async def get_player(player_id: str, admin: bool = Depends(get_admin)):
    """获取玩家详情"""
    start_time = time.time()
    logger.info(f"[IN] GET /admin/player/{player_id}")
    
    account = await Account.get_or_none(id=player_id)
    if not account:
        logger.warning(f"[OUT] GET /admin/player/{player_id} - 玩家不存在 - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家不存在"
        )
    
    player_data = await PlayerData.get_or_none(account_id=account.id)
    
    logger.info(f"[OUT] GET /admin/player/{player_id} - 获取成功 - username: {account.username} - 耗时: {time.time() - start_time:.4f}s")
    return {
        "id": str(account.id),
        "username": account.username,
        "server_id": account.server_id,
        "is_banned": account.is_banned,
        "created_at": account.created_at.isoformat(),
        "last_online_at": player_data.updated_at.isoformat() if player_data else None,
        "game_data": player_data.data if player_data else None
    }


@router.post("/player/{player_id}/ban", response_model=dict)
async def ban_player(player_id: str, admin: bool = Depends(get_admin)):
    """封号"""
    start_time = time.time()
    logger.info(f"[IN] POST /admin/player/{player_id}/ban")
    
    async with begin_write_lock_by_account_id(
        endpoint=f"POST /api/admin/player/{player_id}/ban",
        account_id=player_id,
        token_version=None,
        lock_player=False,
        allow_missing_account=True,
    ) as locked:
        account = locked.account
        if not account:
            logger.warning(f"[OUT] POST /admin/player/{player_id}/ban - 玩家不存在 - 耗时: {time.time() - start_time:.4f}s")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="玩家不存在"
            )

        account.is_banned = True
        await account.save()
    
    logger.info(f"[OUT] POST /admin/player/{player_id}/ban - 封号成功 - username: {account.username} - 耗时: {time.time() - start_time:.4f}s")
    return {"success": True, "message": "封号成功"}


@router.post("/mail/send", response_model=dict)
async def admin_send_mail(request: AdminMailSendRequest, admin: bool = Depends(get_admin)):
    start_time = time.time()
    logger.info(f"[IN] POST /admin/mail/send - account_id: {request.account_id} - title: {request.title}")
    account = await Account.get_or_none(id=request.account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="玩家不存在")
    result = await MailSystem.create_mail(
        account_id=str(account.id),
        title=request.title,
        content=request.content,
        attachments=[a.dict() for a in request.attachments],
    )
    if not result.get("success", False):
        return result
    logger.info(f"[OUT] POST /admin/mail/send - success - 耗时: {time.time() - start_time:.4f}s")
    return result


@router.post("/mail/send_batch", response_model=dict)
async def admin_send_mail_batch(request: AdminMailSendBatchRequest, admin: bool = Depends(get_admin)):
    start_time = time.time()
    logger.info(
        f"[IN] POST /admin/mail/send_batch - all_accounts: {request.all_accounts} - "
        f"targets: {len(request.account_ids)} - title: {request.title}"
    )
    target_ids: list[str] = []
    if request.all_accounts:
        accounts = await Account.all()
        target_ids = [str(a.id) for a in accounts]
    else:
        target_ids = [str(x) for x in request.account_ids if str(x).strip()]

    sent_count = 0
    skipped_capacity = 0
    for account_id in target_ids:
        result = await MailSystem.create_mail(
            account_id=account_id,
            title=request.title,
            content=request.content,
            attachments=[a.dict() for a in request.attachments],
        )
        if result.get("success", False):
            sent_count += 1
        elif result.get("reason_code") == "MAIL_CAPACITY_REACHED":
            skipped_capacity += 1
    response = {
        "success": True,
        "reason_code": "MAIL_SEND_BATCH_SUCCEEDED",
        "reason_data": {
            "target_count": len(target_ids),
            "sent_count": sent_count,
            "skipped_capacity": skipped_capacity,
        },
    }
    logger.info(f"[OUT] POST /admin/mail/send_batch - {response} - 耗时: {time.time() - start_time:.4f}s")
    return response
