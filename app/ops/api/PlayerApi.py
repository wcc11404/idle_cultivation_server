from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.ops.audit import OpsAuditService
from app.ops.auth import require_ops_permission, get_current_ops_user
from app.ops.models import OpsUser
from app.ops.services import PlayerOpsService

router = APIRouter()


class AccountActionRequest(BaseModel):
    account_id: str = Field(min_length=1)


@router.get("/players", response_model=dict)
async def ops_players(
    q: str = "",
    page: int = 1,
    page_size: int = 20,
    _: OpsUser = Depends(require_ops_permission("player.view")),
):
    return await PlayerOpsService.list_players(query=q, page=page, page_size=page_size)


@router.get("/players/{account_id}", response_model=dict)
async def ops_player_detail(
    account_id: str,
    _: OpsUser = Depends(require_ops_permission("player.view")),
):
    return await PlayerOpsService.get_player_detail(account_id)


@router.post("/players/ban", response_model=dict)
async def ops_ban_player(
    payload: AccountActionRequest,
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("player.ban")),
):
    result = await PlayerOpsService.ban_player(payload.account_id)
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="player_ban",
        target_scope="single",
        target_payload={"account_id": payload.account_id},
        request_payload=payload.model_dump(),
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.post("/players/unban", response_model=dict)
async def ops_unban_player(
    payload: AccountActionRequest,
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("player.ban")),
):
    result = await PlayerOpsService.unban_player(payload.account_id)
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="player_unban",
        target_scope="single",
        target_payload={"account_id": payload.account_id},
        request_payload=payload.model_dump(),
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.post("/players/kick", response_model=dict)
async def ops_kick_player(
    payload: AccountActionRequest,
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("player.kick")),
):
    result = await PlayerOpsService.kick_player(payload.account_id)
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="player_kick",
        target_scope="single",
        target_payload={"account_id": payload.account_id},
        request_payload=payload.model_dump(),
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result
