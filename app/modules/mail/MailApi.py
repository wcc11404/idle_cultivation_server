"""邮箱 API。"""

import json
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from app.core.Dependencies import GameContext, get_game_context, get_token_info, get_write_game_context
from app.core.Logger import logger
from app.schemas.Game import (
    MailClaimRequest,
    MailClaimResponse,
    MailDeleteRequest,
    MailDeleteResponse,
    MailDetailResponse,
    MailListResponse,
)

from .MailSystem import MailSystem

router = APIRouter()


@router.get("/mail/list", response_model=MailListResponse)
async def mail_list(
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] GET /game/mail/list - token: {token_info['token']} - "
        f"account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )
    result = await MailSystem.list_mails(str(ctx.account.id))
    response = MailListResponse(
        success=bool(result.get("success", False)),
        operation_id="",
        timestamp=time.time(),
        reason_code=str(result.get("reason_code", "")),
        reason_data=result.get("reason_data", {}),
        mails=result.get("mails", []),
        count=int(result.get("count", 0)),
        capacity=int(result.get("capacity", MailSystem.CAPACITY)),
        unread_count=int(result.get("unread_count", 0)),
    )
    logger.info(f"[OUT] GET /game/mail/list - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response


@router.get("/mail/detail", response_model=MailDetailResponse)
async def mail_detail(
    mail_id: str = Query(...),
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] GET /game/mail/detail - mail_id: {mail_id} - token: {token_info['token']} - "
        f"account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )
    result = await MailSystem.get_mail_detail_and_mark_read(str(ctx.account.id), mail_id)
    if result.get("success", False):
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
    response = MailDetailResponse(
        success=bool(result.get("success", False)),
        operation_id="",
        timestamp=time.time(),
        reason_code=str(result.get("reason_code", "")),
        reason_data=result.get("reason_data", {}),
        mail=result.get("mail", {}),
    )
    logger.info(f"[OUT] GET /game/mail/detail - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response


@router.post("/mail/claim", response_model=MailClaimResponse)
async def mail_claim(
    request: MailClaimRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] POST /game/mail/claim - {json.dumps(request.dict(), ensure_ascii=False)} - "
        f"token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )
    result = await MailSystem.claim_mail(str(ctx.account.id), request.mail_id, ctx.inventory_system)
    if result.get("success", False):
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
    response = MailClaimResponse(
        success=bool(result.get("success", False)),
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=str(result.get("reason_code", "")),
        reason_data=result.get("reason_data", {}),
        rewards_granted=result.get("rewards_granted", {}),
    )
    logger.info(f"[OUT] POST /game/mail/claim - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response


@router.post("/mail/delete", response_model=MailDeleteResponse)
async def mail_delete(
    request: MailDeleteRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] POST /game/mail/delete - {json.dumps(request.dict(), ensure_ascii=False)} - "
        f"token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )
    result = await MailSystem.delete_mails(str(ctx.account.id), str(request.delete_mode), request.mail_ids)
    if result.get("success", False):
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
    response = MailDeleteResponse(
        success=bool(result.get("success", False)),
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=str(result.get("reason_code", "")),
        reason_data=result.get("reason_data", {}),
        deleted_count=int(result.get("reason_data", {}).get("deleted_count", 0)),
    )
    logger.info(f"[OUT] POST /game/mail/delete - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response

