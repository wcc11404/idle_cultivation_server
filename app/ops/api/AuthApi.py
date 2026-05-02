from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.ops.audit import OpsAuditService
from app.ops.auth import OpsAuthService, get_current_ops_user, ops_security
from app.ops.models import OpsUser

router = APIRouter()


class OpsLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


@router.post("/auth/login", response_model=dict)
async def ops_login(request: OpsLoginRequest, raw_request: Request):
    result = await OpsAuthService.login(request.username, request.password)
    await OpsAuditService.write_log(
        operator=None,
        action_type="ops_login",
        target_scope="self",
        target_payload={"username": request.username},
        request_payload={"username": request.username},
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.post("/auth/logout", response_model=dict)
async def ops_logout(
    raw_request: Request,
    credentials=Depends(ops_security),
    current_user: OpsUser = Depends(get_current_ops_user),
):
    result = await OpsAuthService.logout(credentials.credentials)
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="ops_logout",
        target_scope="self",
        target_payload={"username": current_user.username},
        request_payload={},
        result="success",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.get("/auth/me", response_model=dict)
async def ops_me(current_user: OpsUser = Depends(get_current_ops_user)):
    return {
        "success": True,
        "reason_code": "OPS_ME_SUCCEEDED",
        "reason_data": {},
        "user": OpsAuthService.serialize_user(current_user),
    }
