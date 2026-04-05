"""
历练相关 API（优化版本）

使用依赖注入和响应构建辅助函数，减少重复代码
"""

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import (
    LianliBattleRequest, LianliBattleResponse,
    LianliSettleRequest, LianliSettleResponse
)
from app.core.Security import security
from app.core.Dependencies import get_game_context, get_token_info, GameContext
from app.core.Logger import logger
from datetime import datetime, timezone
from typing import Any, Dict
import time
import json

router = APIRouter()


def _build_lianli_battle_failure_response(
    operation_id: str,
    timestamp: float,
    message: str
) -> LianliBattleResponse:
    """构建历练战斗失败响应"""
    return LianliBattleResponse(
        success=False,
        operation_id=operation_id,
        timestamp=timestamp,
        battle_timeline=[],
        total_time=0.0,
        player_health_before=0.0,
        player_health_after=0.0,
        enemy_health_after=0.0,
        enemy_data={},
        victory=False,
        loot=[],
        message=message
    )


def _build_lianli_battle_success_response(
    operation_id: str,
    timestamp: float,
    result: Dict[str, Any]
) -> LianliBattleResponse:
    """构建历练战斗成功响应"""
    return LianliBattleResponse(
        success=result.get("success", True),
        operation_id=operation_id,
        timestamp=timestamp,
        battle_timeline=result.get("battle_timeline", []),
        total_time=result.get("total_time", 0.0),
        player_health_before=result.get("player_health_before", 0.0),
        player_health_after=result.get("player_health_after", 0.0),
        enemy_health_after=result.get("enemy_health_after", 0.0),
        enemy_data=result.get("enemy_data", {}),
        victory=result.get("victory", False),
        loot=result.get("loot", []),
        message=result.get("reason", "战斗模拟完成")
    )


def _build_lianli_settle_response(
    operation_id: str,
    timestamp: float,
    result: Dict[str, Any]
) -> LianliSettleResponse:
    """构建历练战斗结算响应"""
    return LianliSettleResponse(
        success=result["success"],
        operation_id=operation_id,
        timestamp=timestamp,
        settled_index=result.get("settled_index", 0),
        total_index=result.get("total_index", 0),
        player_health_after=result.get("player_health_after", 0.0),
        loot_gained=result.get("loot_gained", []),
        exp_gained=result.get("exp_gained", 0),
        message=result.get("reason", result.get("message", ""))
    )


@router.post("/lianli/simulate", response_model=LianliBattleResponse)
async def simulate_battle(
    request: LianliBattleRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """历练战斗模拟（优化版）"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/lianli/battle - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if ctx.player.is_cultivating:
        response_data = _build_lianli_battle_failure_response(
            request.operation_id, request.timestamp, "正在修炼中，无法开始战斗"
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.alchemy_system.is_alchemizing:
        response_data = _build_lianli_battle_failure_response(
            request.operation_id, request.timestamp, "正在炼丹中，无法开始战斗"
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    result = ctx.lianli_system.start_battle_simulation(
        request.area_id, ctx.player, ctx.spell_system
    )
    
    if result["success"]:
        ctx.db_data["lianli_system"] = ctx.lianli_system.to_dict()
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 战斗模拟成功 - account_id: {ctx.account.id} - area_id: {request.area_id}")
    
    response_data = _build_lianli_battle_success_response(
        request.operation_id, request.timestamp, result
    )
    logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/lianli/finish", response_model=LianliSettleResponse)
async def finish_battle(
    request: LianliSettleRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """历练战斗结算（优化版）"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/lianli/finish - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.lianli_system.finish_battle(
        request.speed, request.index, ctx.player, ctx.spell_system, ctx.inventory_system, ctx.account_system
    )
    
    if result["success"]:
        ctx.save()
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 战斗结算成功 - account_id: {ctx.account.id} - settled_index: {result.get('settled_index', 0)}")
    
    response_data = _build_lianli_settle_response(
        request.operation_id, request.timestamp, result
    )
    logger.info(f"[OUT] POST /game/lianli/finish - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
