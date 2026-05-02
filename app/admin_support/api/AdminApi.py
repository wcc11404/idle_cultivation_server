from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List

from app.core.db.Models import Account, PlayerData
from app.ops.auth import OpsAuthService, get_current_ops_user
from app.ops.models import OpsUser
from app.ops.services import PlayerOpsService
from app.game.domain.mail.MailSystem import MailSystem

router = APIRouter()


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
    return await OpsAuthService.login(username, password)


async def get_admin(current_user: OpsUser = Depends(get_current_ops_user)) -> OpsUser:
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OPS_PERMISSION_DENIED")
    return current_user


@router.get("/players", response_model=List[dict])
async def get_players(_: OpsUser = Depends(get_admin)):
    result = await PlayerOpsService.list_players(query="", page=1, page_size=200)
    return [
        {
            "id": item["account_id"],
            "username": item["username"],
            "server_id": item["server_id"],
            "created_at": item["created_at"],
            "last_online_at": item["last_online_at"],
        }
        for item in result.get("items", [])
    ]


@router.get("/player/{player_id}", response_model=dict)
async def get_player(player_id: str, _: OpsUser = Depends(get_admin)):
    detail = await PlayerOpsService.get_player_detail(player_id)
    if not detail.get("success"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="玩家不存在")
    player = detail["player"]
    return {
        "id": player["account_id"],
        "username": player["username"],
        "server_id": player["server_id"],
        "is_banned": player["is_banned"],
        "created_at": player["created_at"],
        "last_online_at": player["last_online_at"],
        "game_data": player["game_data"],
    }


@router.post("/player/{player_id}/ban", response_model=dict)
async def ban_player(player_id: str, _: OpsUser = Depends(get_admin)):
    return await PlayerOpsService.ban_player(player_id)


@router.post("/mail/send", response_model=dict)
async def admin_send_mail(request: AdminMailSendRequest, _: OpsUser = Depends(get_admin)):
    account = await Account.get_or_none(id=request.account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="玩家不存在")
    return await MailSystem.create_mail(
        account_id=str(account.id),
        title=request.title,
        content=request.content,
        attachments=[row.model_dump() for row in request.attachments],
    )


@router.post("/mail/send_batch", response_model=dict)
async def admin_send_mail_batch(request: AdminMailSendBatchRequest, _: OpsUser = Depends(get_admin)):
    if request.all_accounts:
        accounts = await Account.all()
        target_ids = [str(row.id) for row in accounts]
    else:
        target_ids = [str(account_id).strip() for account_id in request.account_ids if str(account_id).strip()]
    sent_count = 0
    skipped_capacity = 0
    for account_id in target_ids:
        result = await MailSystem.create_mail(
            account_id=account_id,
            title=request.title,
            content=request.content,
            attachments=[row.model_dump() for row in request.attachments],
        )
        if result.get("success"):
            sent_count += 1
        elif result.get("reason_code") == "MAIL_CAPACITY_REACHED":
            skipped_capacity += 1
    return {
        "success": True,
        "reason_code": "MAIL_SEND_BATCH_SUCCEEDED",
        "reason_data": {
            "target_count": len(target_ids),
            "sent_count": sent_count,
            "skipped_capacity": skipped_capacity,
        },
    }
