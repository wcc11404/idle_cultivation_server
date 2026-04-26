"""
修炼相关 API

包含突破境界等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.Game import (
    BreakthroughRequest, BreakthroughResponse,
    CultivationStartRequest, CultivationStartResponse,
    CultivationReportRequest, CultivationReportResponse,
    CultivationStopRequest, CultivationStopResponse
)
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Dependencies import get_write_game_context, get_token_info, GameContext
from app.core.Logger import logger
from app.core.AntiCheatSystem import AntiCheatSystem
from app.modules import PlayerSystem, CultivationSystem, InventorySystem, SpellSystem, AccountSystem, AlchemySystem, LianliSystem
from datetime import datetime, timezone
import time
import json
from math import floor

router = APIRouter()


@router.post("/player/breakthrough", response_model=BreakthroughResponse)
async def breakthrough(
    request: BreakthroughRequest,
    ctx: GameContext = Depends(get_write_game_context),
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
        reason_code=result.get("reason_code", ""),
        reason_data={
            "consumed_resources": result.get("costs", {}) if result["success"] else {},
            "missing_resources": result.get("missing_resources", {}) if not result["success"] else {},
            "new_realm": result.get("new_realm", ctx.player.realm) if result["success"] else "",
            "new_level": result.get("new_level", ctx.player.realm_level) if result["success"] else 0,
            "current_realm": ctx.player.realm if not result["success"] else "",
            "current_level": ctx.player.realm_level if not result["success"] else 0
        }
    )
    logger.info(f"[OUT] POST /game/player/breakthrough - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/player/cultivation/start", response_model=CultivationStartResponse)
async def start_cultivation(
    request: CultivationStartRequest,
    ctx: GameContext = Depends(get_write_game_context),
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
            reason_code="CULTIVATION_START_ALREADY_ACTIVE",
            reason_data={}
        )
        logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.lianli_system.is_battling:
        response_data = CultivationStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="CULTIVATION_START_BLOCKED_BY_BATTLE",
            reason_data={}
        )
        logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.alchemy_system.is_alchemizing:
        response_data = CultivationStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="CULTIVATION_START_BLOCKED_BY_ALCHEMY",
            reason_data={}
        )
        logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data

    if ctx.herb_system.is_gathering:
        response_data = CultivationStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="CULTIVATION_START_BLOCKED_BY_HERB_GATHERING",
            reason_data={}
        )
        logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    current_time = time.time()
    ctx.player.is_cultivating = True
    ctx.player.last_cultivation_report_time = current_time
    await AntiCheatSystem.reset_suspicious_operations(
        account_id=str(ctx.account.id),
        account_system=ctx.account_system,
        db_player_data=ctx.player_data
    )

    ctx.db_data["player"] = ctx.player.to_dict()
    ctx.db_data["account_info"] = ctx.account_system.to_dict()
    
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()
    
    response_data = CultivationStartResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code="CULTIVATION_START_SUCCEEDED",
        reason_data={}
    )
    logger.info(f"[OUT] POST /game/player/cultivation/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/player/cultivation/report", response_model=CultivationReportResponse)
async def report_cultivation(
    request: CultivationReportRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """上报修炼进度"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/player/cultivation/report - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if not ctx.player.is_cultivating:
        response_data = CultivationReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="CULTIVATION_REPORT_NOT_ACTIVE",
            reason_data={},
            spirit_gained=0.0,
            health_gained=0.0,
            used_count_gained=0
        )
        logger.info(f"[OUT] POST /game/player/cultivation/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    current_time = time.time()
    
    tolerance = 0.1
    is_valid, reason = AntiCheatSystem.validate_cultivation_report(
        current_time=current_time,
        last_report_time=ctx.player.last_cultivation_report_time,
        reported_elapsed_seconds=request.elapsed_seconds,
        tolerance=tolerance
    )
    
    if not is_valid:
        anti_cheat_result = await AntiCheatSystem.record_suspicious_operation(
            account_id=str(ctx.account.id),
            operation_type="cultivation_report",
            detail=reason,
            account_system=ctx.account_system,
            db_player_data=ctx.player_data,
            db_account=ctx.account
        )
        
        response_data = CultivationReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="CULTIVATION_REPORT_TIME_INVALID",
            reason_data={
                "reported_elapsed_seconds": round(float(request.elapsed_seconds), 3),
                "actual_interval_seconds": round(current_time - ctx.player.last_cultivation_report_time, 3),
                "max_acceptable_elapsed_seconds": round((current_time - ctx.player.last_cultivation_report_time) * (1 + tolerance), 3),
                "invalid_report_count": anti_cheat_result.get("invalid_count", 0),
                "kicked_out": bool(anti_cheat_result.get("kicked_out", False)),
                "kick_threshold": anti_cheat_result.get("threshold", 10),
            },
            spirit_gained=0.0,
            health_gained=0.0,
            used_count_gained=0
        )
    else:
        carry_before = float(getattr(ctx.player, "cultivation_effect_carry_seconds", 0.0))
        total_elapsed_for_effect = carry_before + float(request.elapsed_seconds)
        whole_seconds = int(floor(total_elapsed_for_effect))
        carry_after = round(max(0.0, total_elapsed_for_effect - whole_seconds), 6)
        logger.info(
            f"[DEBUG] cultivation_report before - account_id: {ctx.account.id} "
            f"health={ctx.player.health} static_max_health={ctx.player.static_max_health} "
            f"spirit={ctx.player.spirit_energy} static_max_spirit={ctx.player.static_max_spirit_energy} "
            f"spell_bonuses={ctx.spell_system.get_attribute_bonuses() if ctx.spell_system else {}} "
            f"reported_elapsed_seconds={request.elapsed_seconds} "
            f"carry_before={carry_before} whole_seconds={whole_seconds}"
        )
        result = CultivationSystem.process_cultivation_tick(
            player=ctx.player,
            delta_seconds=float(whole_seconds),
            spell_system=ctx.spell_system
        )
        ctx.player.cultivation_effect_carry_seconds = carry_after
        await AntiCheatSystem.reset_suspicious_operations(
            account_id=str(ctx.account.id),
            account_system=ctx.account_system,
            db_player_data=ctx.player_data
        )
        logger.info(
            f"[DEBUG] cultivation_report after - account_id: {ctx.account.id} "
            f"health={ctx.player.health} static_max_health={ctx.player.static_max_health} "
            f"spirit={ctx.player.spirit_energy} static_max_spirit={ctx.player.static_max_spirit_energy} "
            f"spirit_gained={result['spirit_gained']} health_gained={result['health_gained']} "
            f"carry_after={carry_after}"
        )
        
        ctx.player.last_cultivation_report_time = current_time
        if whole_seconds > 0:
            ctx.task_system.add_progress("daily_cultivation_seconds", int(whole_seconds))
        
        ctx.db_data["player"] = ctx.player.to_dict()
        ctx.db_data["spell_system"] = ctx.spell_system.to_dict()
        ctx.db_data["task_system"] = ctx.task_system.to_dict()
        ctx.db_data["account_info"] = ctx.account_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        response_data = CultivationReportResponse(
            success=True,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="CULTIVATION_REPORT_SUCCEEDED",
            reason_data={},
            spirit_gained=result["spirit_gained"],
            health_gained=result["health_gained"],
            used_count_gained=result.get("used_count_gained", 0)
        )
    logger.info(f"[OUT] POST /game/player/cultivation/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/player/cultivation/stop", response_model=CultivationStopResponse)
async def stop_cultivation(
    request: CultivationStopRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """停止修炼"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/player/cultivation/stop - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if not ctx.player.is_cultivating:
        response_data = CultivationStopResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="CULTIVATION_STOP_NOT_ACTIVE",
            reason_data={}
        )
        logger.info(f"[OUT] POST /game/player/cultivation/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    ctx.player.is_cultivating = False
    logger.info(
        f"[DEBUG] cultivation_stop - account_id: {ctx.account.id} "
        f"health={ctx.player.health} static_max_health={ctx.player.static_max_health} "
        f"spirit={ctx.player.spirit_energy} static_max_spirit={ctx.player.static_max_spirit_energy} "
        f"spell_bonuses={ctx.spell_system.get_attribute_bonuses() if ctx.spell_system else {}}"
    )
    
    ctx.db_data["player"] = ctx.player.to_dict()
    
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()
    
    response_data = CultivationStopResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code="CULTIVATION_STOP_SUCCEEDED",
        reason_data={}
    )
    logger.info(f"[OUT] POST /game/player/cultivation/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
