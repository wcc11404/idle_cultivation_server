"""
修炼相关 API

包含突破境界等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import (
    BreakthroughRequest, BreakthroughResponse,
    CultivationStartRequest, CultivationStartResponse,
    CultivationReportRequest, CultivationReportResponse,
    CultivationStopRequest, CultivationStopResponse
)
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Dependencies import get_game_context, get_token_info, GameContext
from app.core.Logger import logger
from app.core.AntiCheatSystem import AntiCheatSystem
from app.modules import PlayerSystem, CultivationSystem, InventorySystem, SpellSystem, AccountSystem, AlchemySystem, LianliSystem
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.post("/player/breakthrough", response_model=BreakthroughResponse)
async def breakthrough(
    request: BreakthroughRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """突破境界"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/player/breakthrough - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = CultivationSystem.execute_breakthrough(ctx.player, ctx.inventory_system)
    
    if result["success"]:
        ctx.db_data["player"] = ctx.player.to_dict()
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
    
    response_data = BreakthroughResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        new_realm=result.get("new_realm", ctx.player.realm),
        new_level=result.get("new_level", ctx.player.realm_level),
        remaining_spirit_energy=ctx.player.spirit_energy,
        materials_used=result.get("costs", {}),
        health=ctx.player.health,
        inventory=ctx.inventory_system.to_dict()
    )
    logger.info(f"[OUT] POST /game/player/breakthrough - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/player/cultivation/start", response_model=CultivationStartResponse)
async def start_cultivation(
    request: CultivationStartRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """开始修炼"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/player/cultivation/start - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if ctx.player.is_cultivating:
        response_data = CultivationStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            spirit_gained=0.0,
            health_gained=0.0,
            used_count_gained=0,
            message="已在修炼状态"
        )
        logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.lianli_system.is_battling:
        response_data = CultivationStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            spirit_gained=0.0,
            health_gained=0.0,
            used_count_gained=0,
            message="正在战斗中，无法开始修炼"
        )
        logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.alchemy_system.is_alchemizing:
        response_data = CultivationStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            spirit_gained=0.0,
            health_gained=0.0,
            used_count_gained=0,
            message="正在炼丹中，无法开始修炼"
        )
        logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    current_time = time.time()
    ctx.player.is_cultivating = True
    ctx.player.last_cultivation_report_time = current_time
    
    result = CultivationSystem.process_cultivation_tick(
        player=ctx.player,
        delta_seconds=1.0,
        spell_system=ctx.spell_system
    )
    
    ctx.db_data["player"] = ctx.player.to_dict()
    ctx.db_data["spell_system"] = ctx.spell_system.to_dict()
    ctx.db_data["account_info"] = ctx.account_system.to_dict()
    
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()
    
    response_data = CultivationStartResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        spirit_gained=result.get("spirit_gained", 0.0),
        health_gained=result.get("health_gained", 0.0),
        used_count_gained=result.get("used_count_gained", 0),
        message="开始修炼"
    )
    logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/player/cultivation/report", response_model=CultivationReportResponse)
async def report_cultivation(request: CultivationReportRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """上报修炼进度"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/player/cultivation/report - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    player = PlayerSystem.from_dict(db_data.get("player", {}))
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    account_system = AccountSystem.from_dict(db_data.get("account_info", {}))
    
    if not player.is_cultivating:
        response_data = CultivationReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            spirit_gained=0.0,
            health_gained=0.0,
            used_count_gained=0,
            message="当前未在修炼状态"
        )
        logger.info(f"[OUT] POST /game/player/cultivation/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    current_time = time.time()
    
    is_valid, reason = AntiCheatSystem.validate_cultivation_report(
        current_time=current_time,
        last_report_time=player.last_cultivation_report_time,
        reported_count=request.count,
        tolerance=0.1
    )
    
    if not is_valid:
        await AntiCheatSystem.record_suspicious_operation(
            account_id=str(current_user.id),
            operation_type="cultivation_report",
            detail=reason,
            account_system=account_system,
            db_player_data=player_data
        )
        
        response_data = CultivationReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            spirit_gained=0.0,
            health_gained=0.0,
            used_count_gained=0,
            message=f"修炼上报异常：{reason}"
        )
    else:
        result = CultivationSystem.process_cultivation_tick(
            player=player,
            delta_seconds=float(request.count),
            spell_system=spell_system
        )
        
        player.last_cultivation_report_time = current_time
        
        db_data["player"] = player.to_dict()
        db_data["spell_system"] = spell_system.to_dict()
        db_data["account_info"] = account_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        response_data = CultivationReportResponse(
            success=True,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            spirit_gained=result["spirit_gained"],
            health_gained=result["health_gained"],
            used_count_gained=result.get("used_count_gained", 0),
            message="修炼成功"
        )
    logger.info(f"[OUT] POST /game/player/cultivation/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/player/cultivation/stop", response_model=CultivationStopResponse)
async def stop_cultivation(request: CultivationStopRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """停止修炼"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/player/cultivation/stop - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    player = PlayerSystem.from_dict(db_data.get("player", {}))
    
    if not player.is_cultivating:
        response_data = CultivationStopResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            message="当前未在修炼状态"
        )
        logger.info(f"[OUT] POST /game/player/cultivation/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    player.is_cultivating = False
    
    db_data["player"] = player.to_dict()
    
    player_data.data = db_data
    player_data.last_online_at = datetime.now(timezone.utc)
    await player_data.save()
    
    response_data = CultivationStopResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        message="停止修炼"
    )
    logger.info(f"[OUT] POST /game/player/cultivation/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
