from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.ops.audit import OpsAuditService
from app.ops.auth import require_ops_permission
from app.ops.models import OpsUser
from app.ops.services import SystemOpsService

router = APIRouter()


class LoginGateRequest(BaseModel):
    enabled: bool
    note: str = ""


class WhitelistUpdateRequest(BaseModel):
    action: str = Field(pattern="^(add|remove)$")
    account_id: str = Field(min_length=1)
    note: str = ""


class KickAllRequest(BaseModel):
    note: str = ""


@router.get("/system/health", response_model=dict)
async def ops_health(_: OpsUser = Depends(require_ops_permission("system.view"))):
    return await SystemOpsService.get_health()


@router.get("/system/summary", response_model=dict)
async def ops_summary(_: OpsUser = Depends(require_ops_permission("system.view"))):
    return await SystemOpsService.get_summary()


@router.post("/system/login-gate", response_model=dict)
async def ops_login_gate(
    payload: LoginGateRequest,
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("system.control")),
):
    result = await SystemOpsService.update_login_gate(
        enabled=payload.enabled,
        operator_username=current_user.username,
        note=payload.note,
    )
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="system_login_gate_update",
        target_scope="system",
        target_payload={"enabled": payload.enabled},
        request_payload=payload.model_dump(),
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.get("/system/whitelist", response_model=dict)
async def ops_whitelist(_: OpsUser = Depends(require_ops_permission("system.view"))):
    return await SystemOpsService.list_whitelist()


@router.post("/system/whitelist", response_model=dict)
async def ops_whitelist_update(
    payload: WhitelistUpdateRequest,
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("system.control")),
):
    result = await SystemOpsService.update_whitelist(
        action=payload.action,
        account_id=payload.account_id,
        operator_username=current_user.username,
        note=payload.note,
    )
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="system_whitelist_update",
        target_scope="system",
        target_payload={"account_id": payload.account_id, "action": payload.action},
        request_payload=payload.model_dump(),
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.post("/system/kick-all", response_model=dict)
async def ops_kick_all(
    payload: KickAllRequest,
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("player.kick")),
):
    result = await SystemOpsService.kick_all_players()
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="player_kick_all",
        target_scope="all",
        target_payload={"all_players": True},
        request_payload=payload.model_dump(),
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result
