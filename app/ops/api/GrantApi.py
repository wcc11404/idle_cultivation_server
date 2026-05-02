from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.ops.audit import OpsAuditService
from app.ops.auth import require_ops_permission
from app.ops.models import OpsUser
from app.ops.services import GrantOpsService

router = APIRouter()


class OpsMailAttachment(BaseModel):
    item_id: str
    count: int = Field(default=1, ge=1)


class GrantMailPreviewRequest(BaseModel):
    account_ids: list[str] = Field(default_factory=list)
    all_accounts: bool = False
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    attachments: list[OpsMailAttachment] = Field(default_factory=list)


class ConfirmRequest(BaseModel):
    confirm_token: str = Field(min_length=1)


@router.post("/grant/mails/preview", response_model=dict)
async def ops_preview_mails(
    payload: GrantMailPreviewRequest,
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("grant.mail")),
):
    result = await GrantOpsService.preview_mail(
        operator_user_id=str(current_user.id),
        title=payload.title,
        content=payload.content,
        attachments=[row.model_dump() for row in payload.attachments],
        account_ids=payload.account_ids,
        all_accounts=payload.all_accounts,
    )
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="grant_mail_preview",
        target_scope="all" if payload.all_accounts else "batch",
        target_payload={"account_ids": payload.account_ids, "all_accounts": payload.all_accounts},
        request_payload=payload.model_dump(),
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.post("/grant/mails/confirm", response_model=dict)
async def ops_confirm_mails(
    payload: ConfirmRequest,
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("grant.mail")),
):
    result = await GrantOpsService.confirm_mail(confirm_token=payload.confirm_token)
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="grant_mail_confirm",
        target_scope="confirm",
        target_payload={"confirm_token": payload.confirm_token},
        request_payload=payload.model_dump(),
        result="success" if result.get("success") else "failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.get("/grant/item-options", response_model=dict)
async def ops_grant_item_options(_: OpsUser = Depends(require_ops_permission("grant.mail"))):
    return GrantOpsService.list_mail_attachment_options()


@router.post("/grant/items/preview", response_model=dict)
async def ops_preview_items_disabled(
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("grant.item")),
):
    result = GrantOpsService.direct_item_grant_disabled()
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="grant_items_preview_disabled",
        target_scope="all",
        target_payload={},
        request_payload={},
        result="failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result


@router.post("/grant/items/confirm", response_model=dict)
async def ops_confirm_items_disabled(
    raw_request: Request,
    current_user: OpsUser = Depends(require_ops_permission("grant.item")),
):
    result = GrantOpsService.direct_item_grant_disabled()
    await OpsAuditService.write_log(
        operator=current_user,
        action_type="grant_items_confirm_disabled",
        target_scope="all",
        target_payload={},
        request_payload={},
        result="failed",
        reason_code=result.get("reason_code"),
        request=raw_request,
    )
    return result
